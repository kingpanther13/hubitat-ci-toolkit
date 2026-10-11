package drivers

import spock.lang.Specification
import spock.lang.Unroll
import support.DriverHarness

class ExampleDriverSpec extends Specification {
    DriverHarness driver = new DriverHarness(new File('drivers/example-driver.groovy'), new File('libraries'))

    def 'install starts off at zero'() {
        when:
        driver.script.installed()

        then:
        driver.events == [[name: 'switch', value: 'off'], [name: 'level', value: 0, unit: '%']]
    }

    def 'switch commands emit the requested switch event'() {
        when:
        driver.script.on()
        driver.script.off()

        then:
        driver.events == [[name: 'switch', value: 'on'], [name: 'switch', value: 'off']]
    }

    @Unroll
    def 'setLevel #requested emits bounded level #expected and switch #switchValue'() {
        when:
        driver.script.setLevel(requested)

        then:
        driver.events == [[name: 'level', value: expected, unit: '%'], [name: 'switch', value: switchValue]]

        where:
        requested | expected | switchValue
        -10       | 0        | 'off'
        0         | 0        | 'off'
        42        | 42       | 'on'
        100       | 100      | 'on'
        125       | 100      | 'on'
    }

}
