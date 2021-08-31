import csv
import datetime

data = []
with open('gemini_BTCUSD_2020_1min.csv') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    for row in spamreader:
        dataPoint = {}
        dataPoint['timestamp'] = datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
        dataPoint['price'] = float(row[3])
        dataPoint['volume'] = float(row[7])
        data.append(dataPoint)

dataReversed = []
for i in range(len(data)-1, 0, -1):
    dataReversed.append(data[i])

benchmark = 1000.0
trial1 = 1000.0
trial1Added = 0.0
prevValue = dataReversed[20]['price']
maxAdded = 0
num = 0
for i in range(20, len(dataReversed)):
    dataPoint = dataReversed[i]
    price = dataPoint['price']
    volume = dataPoint['volume']
    multiplier = price / prevValue
    benchmark = benchmark*multiplier
    trial1 = trial1*multiplier
    prevMovingAverage = sum([p['price'] for p in dataReversed[i-20:i-10]])/10.0
    movingAverage = sum([p['price'] for p in dataReversed[i-10:i]])/10.0
    volumeAverage = sum([p['volume'] for p in dataReversed[i-20:i]])/20.0
    movingAverageAngle = movingAverage/prevMovingAverage

    # print(benchmark)
    if volume > volumeAverage*3:
        
        if movingAverageAngle > 1.01:
            
            trial1 = trial1 + 100.0
            trial1Added = trial1Added + 100.0

        if movingAverageAngle < 0.99 and trial1 >= 10:
            trial1 = trial1 - 100.0
            trial1Added = trial1Added - 100.0

    maxAdded = max(maxAdded, trial1Added)
    benchmarkPercentUp = benchmark/1000.0
    benchMarkAdjusted = benchmarkPercentUp * (maxAdded + 1000.0)
    
    print("Benchmark:", benchMarkAdjusted)
    print("Trial1:", trial1, trial1Added)
    print("Max Float:", maxAdded)
    print("Moving Average:", movingAverage)

    prevValue = dataPoint['price']
    
# print(num)