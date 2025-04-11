import asyncio
import json
from datetime import datetime, timedelta
from main import (
    inquery_stock_price,
    inquery_balance,
    order_stock,
    inquery_order_list,
    inquery_order_detail,
    inquery_stock_info,
    inquery_stock_history,
    inquery_stock_ask,
    inquery_stock_market,
    order_overseas_stock,
    inquery_overseas_stock_price
)

async def test_domestic_stock(symbol: str, name: str):
    """Test domestic stock price inquiry
    
    Args:
        symbol: Stock symbol (e.g. "005930")
        name: Stock name (e.g. "Samsung Electronics")
    """
    try:
        result = await inquery_stock_price(symbol=symbol)
        print(f"\n{name} ({symbol}):")
        print(f"Current price: {result['stck_prpr']}")
        print(f"Change: {result['prdy_vrss']} ({result['prdy_ctrt']}%)")
        print(f"Volume: {result['acml_vol']}")
        print(f"Trading value: {result['acml_tr_pbmn']}")
    except Exception as e:
        print(f"Error in {name} test: {str(e)}")

async def test_balance():
    """Test balance inquiry"""
    try:
        result = await inquery_balance()
        print("\nAccount Balance Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error testing balance: {e}")

async def test_order_stock():
    """Test stock order"""
    try:
        # 시장가 매수
        result = await order_stock("005930", 1, 0, "buy")
        print("\nMarket Price Buy Order Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 지정가 매수
        result = await order_stock("005930", 1, 55000, "buy")
        print("\nLimit Price Buy Order Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # 시장가 매도
        result = await order_stock("005930", 1, 0, "sell")
        print("\nMarket Price Sell Order Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error testing stock order: {e}")

async def test_overseas_order():
    """Test overseas stock order"""
    try:
        # AAPL 지정가 매수
        result = await order_overseas_stock(
            symbol="AAPL",
            quantity=1,
            price=150.00,
            order_type="buy",
            market="NASD"
        )
        print("\nOverseas Stock Buy Order Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # AAPL 현재가 조회
        result = await inquery_overseas_stock_price(
            symbol="AAPL",
            market="NASD"
        )
        print("\nOverseas Stock Price Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error testing overseas stock order: {e}")

async def test_order_list():
    """Test order list inquiry"""
    try:
        # 오늘 날짜로 테스트
        today = datetime.now().strftime("%Y%m%d")
        result = await inquery_order_list(today, today)
        print("\nOrder List Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error testing order list: {e}")

async def test_order_detail():
    """Test order detail inquiry"""
    try:
        # 오늘 날짜로 테스트
        today = datetime.now().strftime("%Y%m%d")
        result = await inquery_order_detail("", today)  # 주문번호 없이 테스트
        print("\nOrder Detail Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error testing order detail: {e}")

async def test_stock_info():
    """Test stock info inquiry"""
    try:
        # 삼성전자 1주일 데이터 테스트
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        result = await inquery_stock_info("005930", start_date, end_date)
        print("\nStock Info Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error testing stock info: {e}")

async def test_stock_history():
    """Test stock history inquiry"""
    try:
        # 삼성전자 1주일 데이터 테스트
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        result = await inquery_stock_history("005930", start_date, end_date)
        print("\nStock History Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error testing stock history: {e}")

async def test_stock_ask():
    """Test stock ask price inquiry"""
    try:
        # 삼성전자 호가 테스트
        result = await inquery_stock_ask("005930")
        print("\nStock Ask Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error testing stock ask: {e}")

async def test_stock_market():
    """Test stock market index inquiry"""
    try:
        result = await inquery_stock_market()
        print("\nStock Market Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error testing stock market: {e}")

async def main():
    """Run all tests"""
    print("Starting KIS MCP Server tests...")
    
    # Domestic stock tests
    await test_domestic_stock("005930", "Samsung Electronics")
    await test_balance()
    await test_order_stock()
    await test_order_list()
    await test_order_detail()
    await test_stock_info()
    await test_stock_history()
    await test_stock_ask()
    await test_stock_market()
    
    # Overseas stock tests
    await test_overseas_order()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 
    