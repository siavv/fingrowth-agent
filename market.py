def get_market_summary():
    try:
        import akshare as ak
        df_stock = ak.stock_zh_index_daily(symbol="sh000300")
        close_stock = df_stock["close"]
        stock_change = (close_stock.iloc[-1] - close_stock.iloc[-20]) / close_stock.iloc[-20] * 100
        
        try:
            df_gold = ak.spot_hist_sge(symbol="Au99.99")
            close_gold = df_gold["close"]
            gold_change = (close_gold.iloc[-1] - close_gold.iloc[-20]) / close_gold.iloc[-20] * 100
            return (f"【真实市场数据】沪深300近20个交易日涨跌幅约 {stock_change:.2f}%；"
                    f"黄金Au99.99近20个交易日涨跌幅约 {gold_change:.2f}%（来源：akshare 公开接口）")
        except Exception:
            return f"【真实市场数据】沪深300近20个交易日涨跌幅约 {stock_change:.2f}%（来源：akshare 公开接口）"
    except Exception:
        return "近期权益市场震荡调整，黄金等避险资产关注度上升（备用数据）"