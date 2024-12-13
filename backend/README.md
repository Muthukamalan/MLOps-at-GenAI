<!-- docker pull pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime -->

```bash
torch-model-archiver --model-name sd3 --version 1.0 --handler sd3_handler.py --extra-files sd3-model.zip -r requirements.txt  --archive-format zip-store
mv sd3.mar model_store/
```

```bash
torchserve --start --ts-config=config.properties --model-store model_store --models sd3=sd3.mar --disable-token-auth --ncs --enable-model-api 
## --ncs --no-config-snapshots
## --foreground
 
torchserve --stop 
```

**network commands**
```bash
nmcli device show
nmcli device show $DEVICE_NAME
nmcli device down $DEVICE_NAME
nmcli device up $DEVICE_NAME
```

> ![NOTE] Address
> inference_address=8080
> management_address=8081
> metrics_address=8082

```bash

# metrics API
curl http://localhost:8082/metrics


# management API
curl http://localhost:8081/models
curl -v -X PUT "http://localhost:8081/models/sd3?min_workers=1&batch_size=10"
curl http://localhost:8081/models/sd3 ## info about models


#  inference API
curl http://localhost:8080/ping                                     ## returns `healthy`
curl -X OPTIONS http://localhost:8080 > swagger.json                ## get swaggers.json
curl http://localhost:8080/predictions/sd3 -F 'data=@prompts.txt'   ## send bunch of  text
curl http://localhost:8080/predictions/sd3?text=cat                 ## send single text
```


```python
import requests
res = requests.post(
            "http://localhost:8080/predictions/sd3",
            files={
                'data':open(r'/GitHub/MLOps/FastAPI/SD3/prompts.txt')
            }
        )
print(res)
```
