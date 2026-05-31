# 测试运行与变更报告

时间: 2026-05-30

变更摘要:
- 新增集成测试脚本输出: `test_api_output_full.txt`
- 新增终端与 uvicorn 日志: `uvicorn_terminal_and_runs.txt`

目的:
- 保存本地功能测试的请求/响应和服务器日志以便复现与审计。

主要发现:
- `/api/recommend` 与 `/api/backtest_batch` 已返回 200 并包含预期结构。
- 在某些运行中，测试脚本出现连接超时（可能与服务器短暂不可达或并发负载有关）。

下一步建议:
1. 若需长期保存日志，移动到 `logs/` 目录并在 `.gitignore` 中保留索引或归档策略。
2. 将长时间或大规模并行回测改为异步任务队列（Redis + RQ/Celery）。
3. 添加性能基准脚本，测量 `MAX_BACKTEST_WORKERS` 不同值下的吞吐量和延迟。

提交信息: chore: add test API outputs and uvicorn logs
