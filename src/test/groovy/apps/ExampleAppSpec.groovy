package apps

import me.biocomp.hubitat_ci.api.app_api.AppExecutor
import me.biocomp.hubitat_ci.app.HubitatAppSandbox
import me.biocomp.hubitat_ci.app.HubitatAppScript
import me.biocomp.hubitat_ci.validation.Flags
import spock.lang.Specification
import support.IncludeResolver
import support.PermissiveLog
import support.SubscriptionRecorder
import support.TestDevice

/** Runs actual app methods inside the pinned HubitatCI sandbox, with no hub or network. */
class ExampleAppSpec extends Specification {
    HubitatAppScript script
    final SubscriptionRecorder subscriptions = new SubscriptionRecorder()
    final TestDevice sensor = new TestDevice(id: 1, label: 'Hall motion')
    final TestDevice lamp = new TestDevice(id: 2, label: 'Hall light')
    final Map settings = [motionSensors: [sensor], targetSwitches: [lamp]]
    final Map state = [:]
    int unsubscribes = 0

    def setup() {
        def api = Mock(AppExecutor) {
            getState() >> state
            getSettings() >> settings
            getLog() >> new PermissiveLog()
            unsubscribe() >> { unsubscribes++; subscriptions.reset() }
            subscribe(_, _ as String, _ as String) >> { args ->
                subscriptions.record(args[0], args[1] as String, args[2] as String)
            }
        }
        File source = new File('apps/example-app.groovy')
        def sandbox = new HubitatAppSandbox(IncludeResolver.resolve(
            source.getText('UTF-8'), new File('libraries')))
        Map options = [
            api: api,
            userSettingValues: settings,
            validationFlags: [Flags.DontValidatePreferences, Flags.DontValidateDefinition,
                              Flags.DontRestrictGroovy, Flags.DontRunScript]
        ]
        // The eighty20results fork requires a child-app resolver even for a childless app.
        // joelwetzel rejects the option; the standalone 2.5 build selects its fork explicitly.
        if (System.getProperty('hubitatCiFork', 'eighty20results') == 'eighty20results') {
            options.childAppResolver = { String namespace, String name ->
                throw new IllegalStateException('This sample does not create child apps')
            }
        }
        script = sandbox.run(options)
    }

    def 'install subscribes the selected sensor and active motion turns the selected switch on'() {
        when:
        script.installed()
        subscriptions.fireEvent(script, sensor, 'motion', 'active')

        then:
        subscriptions.subscriptions*.source == [sensor]
        subscriptions.subscriptions*.attribute == ['motion']
        subscriptions.subscriptions*.handler == ['motionHandler']
        lamp.commands == [[name: 'on', arguments: []]]
    }

    def 'inactive motion turns every selected switch off'() {
        given:
        def secondLamp = new TestDevice(id: 3)
        settings.targetSwitches = [lamp, secondLamp]
        script.installed()

        when:
        subscriptions.fireEvent(script, sensor, 'motion', 'inactive')

        then:
        lamp.commands == [[name: 'off', arguments: []]]
        secondLamp.commands == [[name: 'off', arguments: []]]
    }

    def 'update replaces old subscriptions and repeated updates do not duplicate handlers'() {
        given:
        script.installed()
        def replacement = new TestDevice(id: 4)
        settings.motionSensors = [replacement]

        when:
        script.updated()
        script.updated()

        then:
        unsubscribes == 2
        subscriptions.subscriptions*.source == [replacement]

        when:
        subscriptions.fireEvent(script, sensor, 'motion', 'active')

        then:
        thrown(IllegalStateException)
        lamp.commands.empty
    }

    def 'unknown motion value leaves switches alone'() {
        when:
        script.motionHandler([value: 'unavailable'])

        then:
        lamp.commands.empty
    }
}
