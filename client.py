import asyncio
from main import inquery_stock_price, load_token

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

async def main():
    """Run all stock price tests"""
    try:
        # Test domestic stocks
        await test_domestic_stock("005930", "Samsung Electronics")
        await test_domestic_stock("009830", "Hanwha Solution")
        
        # Print token info
        print("\nToken info:")
        print(load_token())
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 
    