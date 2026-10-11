package support

/** Loads real driver method bodies; it deliberately does not model Hubitat's driver metadata DSL. */
class DriverHarness {
    final List<Map> events = []
    final Map state = [:]
    final Script script

    DriverHarness(File source, File libraries) {
        def binding = new Binding([
            state: state,
            settings: [:],
            sendEvent: { Map event -> events << new LinkedHashMap(event) },
            log: new PermissiveLog()
        ])
        script = new GroovyShell(binding).parse(
            IncludeResolver.resolve(source.getText('UTF-8'), libraries), source.name)
        // Do not call run(): the parse lane checks syntax; a real hub validates metadata semantics.
    }
}
