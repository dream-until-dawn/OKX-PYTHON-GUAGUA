# OKX-PYTHON-GUAGUA

# 前提

请将 OKX 设置为开平仓模式而非买卖模式,目前仅支持开平仓模式

### 介绍

使用 python 的网络请求库 requests 实现 okx 加密货币交易所的 api 交互

### 使用

```python
python -m build # 打包
pip install --upgrade twine setuptools wheel packaging # 安装 twine、setuptools、 wheel 和packaging
```

#### 测试线

```python
python -m twine upload --repository testpypi dist/* # 上传包到 pypi-test
pip install --index-url https://test.pypi.org/simple/ --no-deps okxpy_guagua # 安装包
```

#### 正式线

```python
python -m twine upload dist/* # 上传包到 pypi
pip install --upgrade okxpy_guagua # 安装包
```
