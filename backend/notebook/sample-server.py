import requests
#################################################################################################################################
# res = requests.post(
#             "http://localhost:8080/predictions/sd3",
#             files={
#                 'data':open(r'/home/muthu/GitHub/MLOps/FastAPI/SD3/prompts.txt')
#             }
#         )

# res = requests.post(
#             "http://localhost:8080/predictions/sd3",
#             data="dramatic swirling cosmos in the sky, Earth glowing like a jewel, violent brushstrokes suggesting dust storms, intense light and shadow contrasts"
#         )

# print(res)

# img = Image.fromarray(np.array(json.loads(res.text),dtype="uint8"))
# img.save("output.jpg")

# curl http://localhost:8080/ping      
# res = requests.get("http://localhost:8080/ping")
# if res.status_code==200:
#     print(res.json())




model_name='sd3'
TORCHSERVE_MANAGEMENT_API = "http://localhost:8081"
min_workers=2
max_workers=4

url = f"{TORCHSERVE_MANAGEMENT_API}/models/{model_name}"
params = {"min_workers": min_workers,'max_workers':max_workers}
res = requests.put(url, params=params)
if res.status_code == 200:
    print({
        'status': "ok",
        "model_details": res.json()  # returning the model's details
    })
else:
    print({'status': "fails", 'error': f"Model {model_name} not found",'err':res})