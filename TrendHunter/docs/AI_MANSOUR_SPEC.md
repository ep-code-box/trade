# AI Mansour Spec & Integration Rule

## [SYSTEM DESIGN]
- **Engine**: MLX-LM with Phi-3.5-mini (4-bit quantized)
- **Interface**: OpenAI Compatible API (via `mlx_lm.server`)
- **Port**: 11434
- **Endpoint**: `/v1/chat/completions`

## [INTEGRATION RULE]
1. **Zero-Loading Delay**: The model MUST be pre-loaded. Any API endpoint calling AI should return an error immediately if the model server is not reachable, rather than attempting to load the model itself.
2. **Data-Driven Personas**:
    - `LIVERMORE`: Focus on Price Action, Pivot Points, and Shield proximity.
    - `ONEIL`: Focus on RS Score, EPS Growth, and Market Leadership.
3. **Deterministic Output**: Use `temperature: 0.1` or lower to ensure consistent quantitative analysis.

## [ORCHESTRATION]
- Use `restart_all.sh` for standard deployment.
- Never include model loading logic within the FastAPI startup sequence of the main trading server. Keep them decoupled.
