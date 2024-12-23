import uuid

class AgentSession:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.data = {}  # Store agent data here

    def update_data(self, data):
        self.data.update(data)

    def get_data(self):
        return self.data

