# Huamengyun QA Automation Demo

这是一个面试展示型的 Python + pytest 自动化测试项目。项目以“华盟云零售 SaaS / 门店经营系统”的业务风格为背景，模拟商品、订单、支付、库存、会员、权限、报表和 AI 智能运营助手等核心链路。

> 说明：本项目只使用本地模拟 API 和演示数据，不包含真实公司接口、账号、数据库或内部资料。

## 项目定位

这个项目适合用于展示：

- 如何围绕业务链路设计接口自动化用例
- 如何用 pytest 组织测试目录、fixture 和断言
- 如何验证金额、订单状态、库存、会员积分等核心业务结果
- 如何覆盖权限控制和敏感数据风险
- 如何把 AI 助手回复与后台报表数据做一致性校验
- 如何通过 GitHub Actions 做基础 CI

## 业务覆盖

| 模块 | 覆盖场景 |
| --- | --- |
| 登录鉴权 | 正常登录、错误密码 |
| 商品管理 | 商品上下架、多端商品展示、价格同步 |
| 订单支付 | 创建订单、优惠金额、支付回调、订单状态流转 |
| 库存扣减 | 支付后库存扣减、退款后库存回补 |
| 会员权益 | 消费积分增加、退款积分回滚、积分流水 |
| 权限控制 | 店员无法查看敏感经营报表，店长可查看 |
| AI 助手 | 经营数据回复与报表一致、无权限兜底、模糊问题兜底 |
| 回归链路 | 商品 -> 下单 -> 支付 -> 报表 -> AI 助手 |

## 项目结构

```text
.
├── huamengyun_qa_demo/
│   ├── fake_api.py          # 本地模拟业务 API
│   ├── models.py            # 业务对象和枚举
│   └── assertions.py        # 通用断言方法
├── tests/
│   ├── api/                 # 单模块接口用例
│   ├── regression/          # 核心业务回归链路
│   └── conftest.py          # pytest fixtures
├── test_data/
│   └── business_cases.json  # 演示测试数据
├── docs/
│   ├── test-strategy.md     # 测试策略说明
│   └── interview-notes.md   # 面试讲解口径
└── .github/workflows/
    └── python-tests.yml     # GitHub Actions
```

## 快速运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

生成 HTML 报告：

```bash
mkdir -p reports
pytest --html=reports/report.html --self-contained-html
```

按标记运行：

```bash
pytest -m smoke
pytest -m ai
pytest -m permission
```

## 示例用例

```python
def test_paid_order_updates_status_amount_inventory_and_points(api, cashier_token, business_cases):
    case = business_cases["bread_order"]
    before_inventory = api.products[case["sku"]].inventory

    order = assert_success(
        api.create_order(
            cashier_token,
            member_id=business_cases["member_id"],
            items=[{"sku": case["sku"], "quantity": case["quantity"]}],
            coupon_amount=case["coupon_amount"],
        )
    )
    paid_order = assert_success(
        api.payment_callback(
            order["orderId"],
            transaction_id="pay_demo_1001",
            pay_amount=order["payAmount"],
        )
    )

    assert paid_order["status"] == "PAID"
    assert paid_order["payAmount"] == "35.00"
    assert api.products[case["sku"]].inventory == before_inventory - case["quantity"]
```

## 面试时可以这样介绍

我做了一个基于华盟云业务风格的 pytest 自动化测试 demo，主要模拟门店 SaaS 系统里的商品、订单、支付、库存、会员、权限和 AI 助手场景。项目重点不是单纯测接口通不通，而是关注业务断言，比如支付后订单状态是否正确、库存是否扣减、会员积分是否增加、退款后是否回滚、多端展示是否一致，以及 AI 助手回答经营数据时是否和后台报表一致。

我目前更倾向于先用 Apifox/Postman 维护接口用例，再用 Python + pytest 把核心链路沉淀成可重复执行的回归用例。这个 demo 就是我对接口自动化和业务回归思路的练习。

