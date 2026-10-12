package server

import me.biocomp.hubitat_ci.api.app_api.AppExecutor
import me.biocomp.hubitat_ci.app.HubitatAppScript
import support.PermissiveLog
import support.WatchdogV31Factory

class WatchdogV31CacheSpec extends WatchdogV31Spec {
    private HubitatAppScript fresh(Map state = [:], Map atomicState = [:],
                                   Map settings = [hubSecurityEnabled: false]) {
        WatchdogV31Factory.create(api: Mock(AppExecutor) {
            _ * getState() >> state
            _ * getAtomicState() >> atomicState
            _ * getSettings() >> settings
            _ * getLog() >> new PermissiveLog()
        }, userSettingValues: settings)
    }

    def 'v3.1 compiles once while each sandbox receives a fresh script instance'() {
        when:
        def first = fresh()
        def second = fresh()
        then:
        !first.is(second)
        first.getClass().is(second.getClass())
        WatchdogV31Factory.compilations == 1
        second.processJsonRpcMessage([jsonrpc: '2.0', id: 1, method: 'initialize', params: [:]])
            .result.serverInfo == [name: 'e2e-deadman-watchdog-v3-1', version: '3.1']
    }

    def 'state atomic state settings and instance overrides do not leak to fresh sandboxes'() {
        given:
        def first = fresh([owner: 'first'], [held: true], [hubSecurityEnabled: false, marker: 'first'])
        first.metaClass.getAdminToolDefinitions = { -> [[name: 'leaked']] }
        when:
        def second = fresh([owner: 'second'], [:], [hubSecurityEnabled: false, marker: 'second'])
        then:
        first.state.owner == 'first'
        second.state.owner == 'second'
        !second.atomicState.held
        second.settings.marker == 'second'
        second.getAdminToolDefinitions()*.name.contains('hub_update_package')
        !second.getAdminToolDefinitions()*.name.contains('leaked')
    }

    def 'feature reset clears every mutable static map and restores nonempty defaults'() {
        given:
        def first = fresh()
        first.MANUAL_WRITE.tool = 'stale'
        first.PACKAGE_PROGRESS.job = [hold: true]
        first.HEALTH_TICK.active = true
        first.LOOPBACK.clear()
        first.LOOPBACK.failStreak = 99
        when:
        WatchdogV31Factory.resetSharedState()
        def second = fresh()
        then:
        second.MANUAL_WRITE == [:]
        second.PACKAGE_PROGRESS == [:]
        second.HEALTH_TICK == [:]
        second.LOOPBACK == [failStreak: 0, lastOkAt: null, streakStartedAt: null]
    }

    def 'feature reset removes class metaclass overrides as well as instance overrides'() {
        given:
        def first = fresh()
        first.getClass().metaClass.getAdminToolDefinitions = { -> [[name: 'class-leak']] }
        first.metaClass.getAdminToolDefinitions = { -> [[name: 'instance-leak']] }
        when:
        WatchdogV31Factory.resetSharedState()
        def second = fresh()
        then:
        second.getAdminToolDefinitions()*.name.contains('hub_update_package')
        !second.getAdminToolDefinitions()*.name.any { it.endsWith('-leak') }
    }

    def 'peer instances within one feature share locks and progress without resetting each other'() {
        given:
        def first = fresh()
        first.PACKAGE_PROGRESS.job = [requestId: 'in-flight']
        when:
        def second = fresh()
        then:
        second.PACKAGE_PROGRESS.job.requestId == 'in-flight'
        first.PACKAGE_DEPLOY_LOCK.is(second.PACKAGE_DEPLOY_LOCK)
    }
}
