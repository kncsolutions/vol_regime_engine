
    # QuantPriceAction
    
    GPU Accelerated Quantitative Chart Pattern Detection Engine.
    
    ## Install
    
    pip install .
    
    ## Example
    
    ```python
    import numpy as np
    from quantpriceaction import QuantPriceAction
    
    data = np.random.randn(200, 2000).cumsum(axis=1)
    
    engine = QuantPriceAction(device="cuda")
    engine.load(data)
    patterns = engine.detect()
    
    print(patterns)
    