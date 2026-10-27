# clean 输入工程修正执行

## Material Passport

- 模式：工程修正与执行；合成Smoke开发数据；不是新增独立确认。
- 用户授权：修正；修正后重新执行。
- 原失败轮次：`D:\dt-talk\experiments\D3f2R_SMOKE_NEW_FINAL_20261021`，完整保留。
- 当前修正位置：`D:\dt-talk\experiments\D3f2R_CLEANFIX_20261021`。
- 工程问题：原CMC入口将clean传入alpha=.1；修正为clean=0、mixed/coherent_sticky=.1，并拒绝错误clean强度。
- 原生engine.run、optimizer、Fisher、回放、门控、参数、中心、种子、原始数据、评价公式和统计阈值不变。

## 成本与来源

独立复制且逐文件校验312条既有产物。只重做24条受影响clean基线；原共享M0复用，新增M0训练为0。

本次新增严格上限24,000步。原失败轮次已消耗394,400步，其中可复用370,400步、失效clean基线消耗24,000步。修正复合Smoke最终应包含394,400步有效工作；含失败成本累计实际418,400步。原失败成本不会从报告中删除。

`REUSE_PROVENANCE.json`、`REUSED_FILES_SHA256.json`、`CORRECTION_TASKS.json`给出复用/替换映射；原完整优化器账本保留在reference，修正轮账本仅继承未失效调用并追加修正调用。原307条恢复记录、336条训练完成记录、原审计失败证据和根因诊断仍在原轮次。

## 核验与门控

先做零SGD的三流输入契约检查：clean原样、错误alpha被拒绝、mixed与既有封存哈希一致、coherent_sticky不变；再冻结所有修正代码与来源。

修正训练完成后，对336条全部产物重新执行独立审计，不删减输入/权重/因果链/逐块得分检查。接受原执行锁只限来源清单中的312个目录，每个阶段还须匹配正确来源锁。

只有原Smoke GO才进入原计划的新Final池；原门槛与比较规则不变。既有Smoke已暴露，修正不能宣传成新增独立证据。扩展/外部验证未具备预先锁定接口的部分继续列为未完成。不修改论文或回复信。

运行入口：`python -B -u -X utf8 correction_owner.py`。主控沿用原训练→独立审计→分析→GO/STOP→打包流程，仅替换Smoke修正训练入口。RAM准入≥2 GiB，所有训练、审计、复用哈希、压缩和核验使用动态worker。

当前使用Codex后台终端会话，未配置Windows服务；执行环境退出仍可能终止进程。中断后保留证据，不盲目重放优化器。
