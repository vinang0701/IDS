import json, os, sys, random
from datetime import datetime, timedelta
from math import sqrt

def load_events(file_path):
    events = {}
    try:
        with open(file_path, 'r') as file:
            # Read the number of events
            num_events = int(file.readline().strip())

            all_lines = file.readlines()
            if len(all_lines) != num_events:
                raise ValueError(f"Expected {num_events} events, but found {len(all_lines)} lines.")
            
            # Reset the file cursor to process lines
            file.seek(0)
            file.readline()

            for _ in range(num_events):
                line = file.readline().strip().split(":")
                event_name = line[0]
                event_type = line[1]
                min_val = float(line[2]) if line[2] else None
                max_val = float(line[3]) if line[3] else None
                weight = int(line[4])
                events[event_name] = {
                    'type': event_type,
                    'min': min_val,
                    'max': max_val,
                    'weight': weight
                }
    except Exception as e:
        print(f"Error reading Events file: {e}")
        sys.exit(1)
    return events

def load_stats(file_path, events, return_warnings=True):
    stats = {}
    warnings = []
    try:
        with open(file_path, 'r') as file:
            # Read the number of events
            num_events = int(file.readline().strip())

            # Check if number of events is consistent with Events.txt
            if num_events != len(events):
                raise ValueError(f"There are {len(events)} events from events file, but stats file indicated {num_events} events.")

            all_lines = file.readlines()
            if len(all_lines) != num_events:
                raise ValueError(f"Expected {num_events} events, but found {len(all_lines)} events.")
            
            # Reset the file cursor to process lines
            file.seek(0)
            file.readline()

            for _ in range(num_events):
                line = file.readline().strip().split(":")
                event_name = line[0]
                mean = float(line[1])
                stddev = float(line[2])

                # Check if the event is missing in Events.txt
                if event_name not in events:
                    raise Exception(f"'{event_name}' is present in Stats.txt but missing in Events.txt.")
                    

                # Get event details
                event_type = events[event_name].get('type')
                min_val = events[event_name].get('min')
                max_val = events[event_name].get('max')
                
                # Get the event type from the events dictionary
                event_type = events.get(event_name, {}).get('type')

                # Check if mean and stddev are within valid ranges
                if min_val is not None and mean < min_val:
                    warnings.append(f"'{event_name}' has a mean ({mean}) below its minimum value ({min_val}).")
                    raise ValueError(f"'{event_name}' has a mean ({mean}) below its minimum value ({min_val}).")
                if max_val is not None and mean > max_val:
                    warnings.append(f"'{event_name}' has a mean ({mean}) above its maximum value ({max_val}).")
                    raise ValueError(f"'{event_name}' has a mean ({mean}) above its maximum value ({max_val}).")
                if stddev <= 0:
                    warnings.append(f"'{event_name}' has an invalid standard deviation ({stddev}). Must be > 0.")
                    

                # Check conditions based on event type and standard deviation
                if return_warnings:
                    if event_type == 'D':  # Discrete event
                        if stddev != int(stddev):
                            warnings.append(f"'{event_name}' is discrete but has a non-integer standard deviation: {stddev}")
                    elif event_type == 'C':  # Continuous event
                        if stddev == int(stddev):
                            warnings.append(f"'{event_name}' is continuous but has an integer standard deviation: {stddev}")

                stats[event_name] = {
                    'mean': mean,
                    'stddev': stddev
                }
    except Exception as e:
        print(f"\nError reading Stats file: {e}")
        raise
    if return_warnings:
        return stats, warnings
    else:
        return stats

def generate_event(event_name, event_config, stats):
    mean = stats[event_name]['mean']
    stddev = stats[event_name]['stddev']
    event_type = event_config['type']
    min_val = event_config['min']
    max_val = event_config['max']

    # Generate the event value using Gaussian distribution
    value = random.gauss(mean, stddev)
    
    # Clamp the value to the specified range
    if min_val is not None:
        value = max(value, min_val)
    if max_val is not None:
        value = min(value, max_val)

    # Handle discrete and continuous types
    if event_type == 'D':  # Discrete event
        value = int(value) # Convert to an integer
    else:  # Continuous event
        value = round(value, 2)  # Keep two decimal places

    return value

def generate_daily_events(events, stats):
    daily_events = {}
    for event_name, event_config in events.items():
        daily_events[event_name] = generate_event(event_name, event_config, stats)
    return daily_events

def calculate_statistics(daily_values):
    statistics = {}
    for event, values in daily_values.items():  # Use the keys from the first day's events
        #values = [daily_events[event] for daily_events in daily_values]
        total = sum(values)  # Total of all values for the event
        mean = total / len(values)  # Mean calculation
        
        # Calculate variance
        variance = sum((x - mean) ** 2 for x in values) / len(values)  # Variance
        stddev = sqrt(variance)  # Standard deviation

        # Store results in a dictionary
        statistics[event] = {
            "total": round(total, 2),
            "mean": round(mean, 2),
            "stddev": round(stddev, 2)
        }

    return statistics

def calculate_anomaly(daily_events, baseline_stats, events):
    anomaly_counter = 0
    details = {}
    for event_name, value in daily_events.items():
        if event_name in baseline_stats:

            baseline_mean = baseline_stats[event_name]['mean']
            baseline_stddev = baseline_stats[event_name]['stddev']
            weight = events[event_name]['weight']

            # Calculate standard deviation-based deviation
            if baseline_stddev > 0:  # Avoid division by zero
                deviation = abs(value - baseline_mean) / baseline_stddev
                weighted_deviation = deviation * weight
                
                details[event_name] = weighted_deviation
                anomaly_counter += weighted_deviation
                

    return anomaly_counter, details

def check_anomalies(daily_events_list_new, baseline_stats, events):
    threshold = 2 * sum(event['weight'] for event in events.values())
    anomaly = []
    for day_index, daily_events in enumerate(daily_events_list_new):
        anomaly_counter, anomaly_details = calculate_anomaly(daily_events, baseline_stats, events)
        status = "OK" if anomaly_counter <= threshold else "!!!!!!!!!!!!!!!!FLAGGED!!!!!!!!!!!!!!!!"
        anomaly.append({
            "date": (datetime.now() + timedelta(days=day_index)).strftime("%Y-%m-%d"),
            "anomaly counter": round(anomaly_counter, 2),
            "threshold": threshold,
            "status": status
        })
    return anomaly

def isFileReadable(fileName):
    # Check if the file exists
    if not os.path.exists(fileName):
        print("File not found. Please try again.\n")
        return False
    
    # Check if the file is a regular file and is readable
    if not os.path.isfile(fileName):
        print("The specified path is not a file. Please try again.\n")
        return False
    
    if not os.access(fileName, os.R_OK):
        print("The file is not readable. Please check permissions and try again.\n")
        return False
    return True

def getValidFile(prompt):
    while True:
        file_path = input(prompt).strip()
        if isFileReadable(file_path):
            return file_path

def validateNewStatsFile(file_path, events):
    while True:
        try:
            return load_stats(file_path, events, return_warnings=False)
        except Exception as e:
            print("New stats file does not match Events.txt format.\n")
            file_path = getValidFile("Please try again with a different file: ")

def restart(events, baseline_stats):
    # Prompt user for new stats file for anomaly detection
    stats = baseline_stats

    new_stats_file = getValidFile("Step 6: Please enter the new stats file for anomaly detection (e.g., Stats_new.txt): ")

    new_stats = validateNewStatsFile(new_stats_file, events)
    
    input("Step 7: New stats file has been read, Press Enter to continue...")

    # Prompt for the number of days to generate activities for the new stats
    while True:
        try:
            num_days_new = int(input("Step 8: Enter the number of days to generate activities for anomaly detection: "))
            break
        except ValueError:
            print("Days must be an integer.\n") 

    # Generate daily events for the specified number of days using new stats
    start_date = datetime.now()
    daily_events_list_new = []
    for day in range(num_days_new):
        current_date = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
        daily_events = generate_daily_events(events, new_stats)
        daily_events_list_new.append(
            {"date": current_date, 
            **daily_events
            })

    # Print all generated daily events in JSON format
    
    print(json.dumps(daily_events_list_new, indent=4))
    with open("live_daily_events.json", "w") as file:
        json.dump(daily_events_list_new, file, indent=4)
    print("Event data for anomaly detection saved to live_daily_events.json")
    input("Step 9: Events generation for anomaly detection completed. Press Enter to continue...") 

    anomaly = check_anomalies(daily_events_list_new, stats, events)
    print(json.dumps(anomaly, indent=4))
    with open("alerts.json", "w") as file:
        json.dump(anomaly, file, indent=4)
    print("Anomaly detections results saved to alerts.json")
    print("Print anomaly detection results complete.\n")    


def main():
    # Validate command-line arguments
    if len(sys.argv) != 4:
        print("Usage: file.py Events.txt Stats.txt Days")
        sys.exit(1)

    events_file = sys.argv[1]
    stats_file = sys.argv[2]
    try:
        num_days = int(sys.argv[3])
    except ValueError:
        print("Days must be an integer.\n")
        sys.exit(1)

    # Load event and stats data
    events = load_events(events_file)
    input("Step 1: Events file read completed. Press Enter to continue...")

    # Add extra line to check if stats file got error
    # If yes, ask user to input new file
    isStatsFileValid = False
    while isStatsFileValid is False:
        try:
            stats, warnings = load_stats(stats_file, events)
            isStatsFileValid = True
        except Exception as e:
            print("Stats file does not match Events.txt format.\n")
            stats_file = input("Please try again with another file: ")

    input("Step 2: Stats file read completed. Press Enter to continue...")
    for warning in warnings:
        print(warning)
    input("Step 3: Inconsistencies checked. Press Enter to continue...")

    # Generate daily events for the specified number of days using original stats
    start_date = datetime.now()
    daily_events_list_original = []
    daily_values = {event_name: [] for event_name in events}

    for day in range(num_days):
        current_date = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
        daily_events = generate_daily_events(events, stats)
        daily_events_list_original.append({"date": current_date, **daily_events})

        for event_name, value in daily_events.items():
            daily_values[event_name].append(value)

    # Calculate statistics for the original daily events
    original_statistics = calculate_statistics(daily_values)

    # Print all generated daily events in JSON format
    print(json.dumps(daily_events_list_original, indent=4))
    with open("logs.json", "w") as file:
        json.dump(daily_events_list_original, file, indent=4)
    print("Event data saved to logs.json")
    input("Step 4: Events generation completed. Press Enter to continue...") 
    
    print(json.dumps(original_statistics, indent=4))
    with open("analysis_results.json", "w") as file:
        json.dump(original_statistics, file, indent=4)
    print("Calculated statistics (total, mean, stddev) results saved to analysis_results.json")
    input("Step 5: Print calculated statistics complete. Press Enter to continue...") 

    # Prompt user for new stats file for anomaly detection
    new_stats_file = getValidFile("Step 6: Please enter the new stats file for anomaly detection (e.g., Stats_new.txt): ")

    new_stats = validateNewStatsFile(new_stats_file, events)
    
    input("Step 7: New stats file has been read, Press Enter to continue...")
    
    # Prompt for the number of days to generate activities for the new stats
    while True:
        try:
            num_days_new = int(input("Step 8: Enter the number of days to generate activities for anomaly detection: "))
            break
        except ValueError:
            print("Days must be an integer.\n")
        

    # Generate daily events for the specified number of days using new stats
    daily_events_list_new = []
    for day in range(num_days_new):
        current_date = (start_date + timedelta(days=day)).strftime('%Y-%m-%d')
        daily_events = generate_daily_events(events, new_stats)
        daily_events_list_new.append(
            {"date": current_date, 
             **daily_events
             })

    # Print all generated daily events in JSON format
    
    print(json.dumps(daily_events_list_new, indent=4))
    with open("live_daily_events.json", "w") as file:
        json.dump(daily_events_list_new, file, indent=4)
    print("Event data for anomaly detection saved to daily_events_new.json")
    input("Step 9: Events generation for anomaly detection completed. Press Enter to continue...") 

    anomaly = check_anomalies(daily_events_list_new, original_statistics, events)
    print(json.dumps(anomaly, indent=4))
    with open("alerts.json", "w") as file:
        json.dump(anomaly, file, indent=4)
    print("Anomaly detections results saved to alerts.json")
    print("Print anomaly detection results complete.\n")
    while True:
        while True:
            prompt = input("Step 10: Do you want to try again with another training statistics file? [Yes/No]: ").strip()
            
            if prompt.lower() == "yes":
                isContinue = True
                break
            elif prompt.lower() == "no":
                isContinue = False
                break
            else:
                print("Invalid input. Please type in a valid option [Yes/No].")
        
        if isContinue:
            print("Restarting from Step 6...\n")
            restart(events, original_statistics)

        else:
            print("Exiting...")
            sys.exit(1)
    

if __name__ == "__main__":
    main()