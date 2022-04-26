import json

for i in range(26):
    if i + 1 != 19:
        dic = dict()
        dic['SimMode'] = 'ComputerVision'
        dic['ApiServerPort'] = str(25030+i+1)
        with open(str(i+1)+'.json', mode='w+') as f:
            f.write(json.dumps(dic))
            
        
