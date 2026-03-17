import paho.mqtt.client as mqtt

def publish_mqtt(broker, topic, value, username=None, password=None):
    client = mqtt.Client()
    if username and password:
        client.username_pw_set(username, password)
    client.connect(broker, 1883, 60)
    client.publish(topic, value)
    client.disconnect()
