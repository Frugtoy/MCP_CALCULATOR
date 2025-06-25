from mcp.server.fastmcp import FastMCP


server = FastMCP("Calculator")

@server.tool()
def add(l_value:float, r_value:float) ->str:
    """
    Выполняет сложение двух чисел типа float
    
    Args:
        l_value: левое число
        r_value: правое число
        
    Returns:
        результат сложения в str формате
    """
    return f"{l_value + r_value}"

@server.tool()
def sub(l_value:float, r_value:float) ->str:
    """
    Выполняет разность двух чисел типа float
    
    Args:
        l_value: левое число
        r_value: правое число
        
    Returns:
        результат разности в str формате
    """
    return f"{l_value - l_value}"

@server.tool()
def mult(l_value:float, r_value:float) ->str:
    """
    Выполняет  умножение чисел типа float
    
    Args:
        l_value: левое число
        r_value: правое число
        
    Returns:
        результат умножения в str формате
    """
    return f"{l_value * r_value}"

@server.tool()
def div(l_value:float, r_value:float) ->str:
    """
    Выполняет деление двух чисел типа float
    
    Args:
        l_value: левое число
        r_value: правое число
        
    Returns:
        результат деления в str формате 
    """
    try:
        return f"{l_value / r_value}"
    except Exception as e:
        return f"Ошибка при делении: {e}"
