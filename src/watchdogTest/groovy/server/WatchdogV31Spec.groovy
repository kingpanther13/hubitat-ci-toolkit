package server

import spock.lang.Specification
import support.WatchdogV31Factory

/** Reset shared app memory at feature boundaries, including Spock data iterations. */
abstract class WatchdogV31Spec extends Specification {
    void setup() { WatchdogV31Factory.resetSharedState() }
    void cleanup() { WatchdogV31Factory.resetSharedState() }
}
