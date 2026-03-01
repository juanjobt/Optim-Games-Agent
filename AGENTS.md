# AGENTS.md

> [!IMPORTANT]
> Este proyecto implementa estrictamente el **Antigravity Framework**.
> Todo Agente de IA DEBE seguir estos pasos antes de realizar cualquier acción:

1. **Identidad**: Lee `.agent/persons/default.md`
2. **Contexto Antigravity**: Consulta la documentación oficial en `https://antigravity.google/docs/` si encuentras conceptos desconocidos.
3. **Reglas de Ejecución**: Contenidos en el directorio `.agent/rules/`. Sona las restricciones correspondientes al stack tecnológico actual.
4. **Capacidades del agente**: Contenidos en el directorio `.agent/skills/`. Cada skill realiza una tarea concreta y aplica las restricciones correspondientes.
5. **Flujos de trabajo completos**: Contenidos en el directorio `.agent/workflows/`. Son los flujos completos que combinan varias skills y rules para lograr un objetivo complejo.
6. **Validación**: Antes de proponer cambios, verifica que no violan los principios de desacoplamiento y testabilidad de Antigravity.

## Notas Importantes

1. **Orden de aplicación**: Rules → Skills → Workflows
2. **Las rules siempre están activas** — Se aplican a todo el contenido generado
3. **Los workflows combinan skills** — Un workflow puede invocar varias skills en secuencia
