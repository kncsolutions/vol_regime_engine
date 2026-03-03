
    import numpy as np
    from quantpriceaction import QuantPriceAction
    
    def test_detection():
        data = np.random.randn(10, 100).cumsum(axis=1)
        model = QuantPriceAction(device="cpu")
        model.load(data)
        result = model.detect()
        assert isinstance(result, dict)
        