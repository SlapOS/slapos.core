from DateTime import DateTime

if context.getSimulationState() in ("started", "stopped"):
  context.deliver()
