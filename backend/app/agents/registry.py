class AgentRegistry:

    _agents = {}

    @classmethod
    def register(
        cls,
        agent,
    ):
        cls._agents[
            agent.name
        ] = agent

    @classmethod
    def get(
        cls,
        name,
    ):
        return cls._agents.get(name)

    @classmethod
    def all(cls):
        return cls._agents