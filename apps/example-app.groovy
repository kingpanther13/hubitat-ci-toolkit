/** Sample app: mirror motion events to a selected group of switches. */
definition(
    name: 'CI Toolkit Motion Switches', namespace: 'toolkit', author: 'Hubitat CI Toolkit',
    description: 'Reusable testing example: selected motion sensors control selected switches.',
    category: 'Convenience', iconUrl: '', iconX2Url: ''
)

preferences {
    section('Devices') {
        input 'motionSensors', 'capability.motionSensor', title: 'Motion sensors', multiple: true, required: true
        input 'targetSwitches', 'capability.switch', title: 'Switches', multiple: true, required: true
    }
}

def installed() { initialize() }
def updated() {
    unsubscribe()
    initialize()
}

def initialize() {
    (settings.motionSensors ?: []).each { sensor ->
        subscribe(sensor, 'motion', 'motionHandler')
    }
}

def motionHandler(event) {
    if (event.value == 'active') {
        (settings.targetSwitches ?: []).each { target -> target.on() }
    } else if (event.value == 'inactive') {
        (settings.targetSwitches ?: []).each { target -> target.off() }
    }
}
