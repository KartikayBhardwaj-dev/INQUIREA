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
    def get(cls, name):

        agent = cls._agents.get(name)

        if not agent:
            raise ValueError(
            f"Agent {name} not registered"
        )

        return agent

    @classmethod
    def all(cls):
        return cls._agents