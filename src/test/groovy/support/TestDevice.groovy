// Adapted from hubitat-local-mcp-server at 0e6094bf (MIT); see reference/provenance.json.
package support

/** Minimal device fixture: commands are recorded; attributes are explicitly seeded by the test. */
class TestDevice {
    Integer id
    String name
    String label
    Map attributeValues = [:]
    final List<Map> commands = []

    Object currentValue(String attribute) { attributeValues[attribute] }
    void on() { invokeCommand('on', []) }
    void off() { invokeCommand('off', []) }
    void setLevel(Integer level) { invokeCommand('setLevel', [level]) }
    void invokeCommand(String command, List arguments) {
        commands << [name: command, arguments: new ArrayList(arguments)]
    }
}
