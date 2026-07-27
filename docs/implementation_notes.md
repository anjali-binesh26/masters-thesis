### Progress
Week of: 20.07
- Reviewed the NetSight architecture and execution flow.
- Identified the responsibilities of the agent components.
- Successfully built the Docker image.
- Verified the project configuration.

Week of: 27.07
- Verified e2e NetSight execution.
- Began use case 1 by analysing Amarisoft QoS configuration.
- Iteratively refined the system prompt to improve the quality and structure of the generated output.

| Run | Observation |
|------|-------------|
| 1 | Completed successfully (239.2 s). Correctly identified QoS parameters but produced very verbose documentation-style output focused primarily on configuration files. |
| 2 | Timed out after prompt modifications. Prompt was too broad and encouraged exhaustive analysis of the documentation. |
| 3 | Completed successfully (193.7 s). Produced concise tabular interface definitions with parameter locations and identified both configuration file and Remote API interfaces. Some API mappings may require manual verification. |


### Current Issue
Configured LLM host (`LLM_HOST=llm`) is not reachable. Seems to be an issue with DHCP connection on device and DNS. Ethernet uses Google DNS to resolve addresses. Temp workaround: hard-coding IP address in .env file.

### Next Steps
- Refine the prompt to reduce inferred API mappings.
- Verify Remote API interface locations against the Amarisoft documentation.
- Develop a generic prompt for simple single-parameter management tasks.
- Parameterise use cases description.
- Extend the prompt for more complex use cases once the basic workflow is stable.
