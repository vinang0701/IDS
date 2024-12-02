# IDS
This is a Python-based intrusion detection system for email servers. It contains the following:
1. Activity Engine
2. Analysis Engine
3. Alert Engine

Note: This is just an example to explain the concepts of an IDS and should not be used for production.

## Run
The format for running the program is as such:

Windows:
```
python IDS.py <Events file> <Stats file> <Number of days>
```
Mac/Linux:
```
python3 IDS.py <Events file> <Stats file> <Number of days>
```

## How it works
Events.txt sets the range of the different events that we will be testing. For example:\
Event name:Discrete or Continuos Stats:Minimum value:Maximum Value:Weight:
```
5
Logins:D:0:20:2:
Time online:C:30:1440:2:
Emails sent:D:0:100:1:
Emails opened:D:1:100:1:
Emails deleted:D:0:100:2:
```

You can adjust the weight to your liking, which will adjust the threshold. The first line indicates the number of events we will be testing so the program can loop and store the events in a dictionary.
<br /><br /><br />
Stats.txt provides the base statistics of how baseline events should behave. For example:\
Event name:Mean:Std dev
```
5
Logins:4:1.5:
Time online:150.5:25.00:
Emails sent:10:3:
Emails opened:12:4.5:
Emails deleted:7:2.25:
```

Ensure that the number of events in Events.txt and Stats.txt match, as well as the event names.
## 1. Activity Engine
The actitity engine generate events for set number of days given Events.txt, Stats.txt and number of days specified when running the program, and saves the data in a JSON file called "logs.json".\
![Alt text](/Screenshots/runIDS.png?raw=true "Run IDS program")

## 2. Analysis Engine
The analysis engine will take the events generated previously an compute the mean and standard deviation. The results will be saved in a JSON file called "analysis.json".\
![Alt text](/Screenshots/analysisEngine.png?raw=true "Analysis Engine Example")

## 3. Alert Engine
The program will prompt you to input a different stats file, similar to the baseline stats file. However, this will be used to generate events for training data. Use the "analysis.json" file to help you decide the values to use for mean and standard deviation. This will help you fine tune the probability of raising alerts.\
![Alt text](/Screenshots/newEventsTestData.png?raw=true "Generate live data")\
![Alt text](/Screenshots/alertEngine.png?raw=true "Alert Engine Example")

