package support

import me.biocomp.hubitat_ci.app.HubitatAppSandbox
import me.biocomp.hubitat_ci.app.HubitatAppScript
import me.biocomp.hubitat_ci.validation.Flags

/** One entry point for the active v3.1 app, with fresh HubitatCI wiring per instance. */
class WatchdogV31Factory {
    private static final String SOURCE = new File('watchdog/e2e-deadman-watchdog-v3-1.groovy').getText('UTF-8')
    private static int compilationCount = 0

    static HubitatAppScript create(Map options) {
        new HubitatAppSandbox(SOURCE).run(options + [validator: new WatchdogValidator()])
    }

    static int getCompilations() { compilationCount }

    static void resetSharedState() {
        // The uncached baseline gets fresh class state from every parse.
    }

    private static class WatchdogValidator extends PassThroughAppValidator {
        WatchdogValidator() {
            super([Flags.DontValidatePreferences, Flags.DontValidateDefinition,
                   Flags.DontRestrictGroovy, Flags.DontRunScript])
        }

        @Override
        HubitatAppScript parseScript(String source, String name = 'Script1') {
            HubitatAppScript script = super.parseScript(source, name)
            compilationCount++
            script
        }
    }
}
