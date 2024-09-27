from flask import Flask, render_template_string, request, Response
import time
import pytz
from datetime import datetime
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

class Stopwatch:
    def __init__(self, timezone_str='US/Mountain'):
        self.start_time = None
        self.intervals = []
        self.prompts = []
        self.timezone = pytz.timezone(timezone_str)
        self.start_times = []  # To store all start times for display

    def start(self):
        if self.start_time is None:
            self.start_time = time.time()
            start_time_log = datetime.fromtimestamp(self.start_time, self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            self.start_times.append(start_time_log)
            return f"START {len(self.start_times)}: {start_time_log}", "running"
        return "Stopwatch is already running.", "running"

    def stop(self):
        if self.start_time is not None:
            end_time = time.time()
            elapsed_time = end_time - self.start_time
            self.intervals.append((end_time, elapsed_time))
            self.start_time = None
            return f"Interval {len(self.intervals)}: {datetime.fromtimestamp(end_time, self.timezone).strftime('%Y-%m-%d %H:%M:%S')}, Duration: {elapsed_time:.2f} seconds", "stopped"
        return "Stopwatch is not running.", "stopped"

    def log_prompts(self):
        if self.start_time is not None:
            prompt_time = time.time()
            elapsed_time = prompt_time - self.start_time
            self.prompts.append((prompt_time, elapsed_time))
            return f"Prompt {len(self.prompts)}: {datetime.fromtimestamp(prompt_time, self.timezone).strftime('%Y-%m-%d %H:%M:%S')}, Duration: {elapsed_time:.2f} seconds", "running"
        return "Stopwatch is not running.", "stopped"

    def reset(self):
        self.start_time = None
        self.intervals = []
        self.prompts = []
        self.start_times = []
        return "Stopwatch has been reset.", "stopped"

    def get_events(self):
        events = []
        # Add all start times to the events
        for i, start_time in enumerate(self.start_times):
            events.append((start_time, f'START {i + 1}', ''))

        # Add intervals with their end times
        for i, (end_time, duration) in enumerate(self.intervals):
            timestamp = datetime.fromtimestamp(end_time, self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            events.append((timestamp, f'Interval {i + 1}', f'{duration:.2f}'))

        # Add prompts with their times
        for i, (prompt_time, duration) in enumerate(self.prompts):
            timestamp = datetime.fromtimestamp(prompt_time, self.timezone).strftime('%Y-%m-%d %H:%M:%S')
            events.append((timestamp, f'Prompt {i + 1}', f'{duration:.2f}'))

        # Sort events by timestamp (which is end_time for intervals and prompt_time for prompts)
        events.sort(key=lambda x: x[0])
        return events

    def generate_log_file(self):
        events = self.get_events()
        log_lines = []
        for timestamp, event_type, duration in events:
            if event_type.startswith('START'):
                log_lines.append(f'{event_type}: {timestamp}')
            else:
                log_lines.append(f'{event_type}: {timestamp}, Duration: {duration} seconds')
        log_content = '\n'.join(log_lines)
        return io.BytesIO(log_content.encode('utf-8'))

stopwatch = Stopwatch(timezone_str='US/Mountain')

@app.route('/', methods=['GET', 'POST'])
def index():
    # Initialize messages
    message = ""
    status_message = ""
    status = "stopped"

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'start':
            message, status = stopwatch.start()
        elif action == 'stop':
            message, status = stopwatch.stop()
        elif action == 'log_prompt':
            message, status = stopwatch.log_prompts()
        elif action == 'reset':
            message, status = stopwatch.reset()
        elif action == 'download_log':
            log_file = stopwatch.generate_log_file()
            return Response(
                log_file,
                mimetype='text/plain',
                headers={"Content-Disposition": "attachment;filename=stopwatch_log.txt"}
            )
        else:
            message = "Invalid action."
            status = "stopped"

    # Update status message with color
    status_color = "green" if status == "running" else "red"
    status_message = f'<strong style="color:{status_color};">Stopwatch is {status.upper()}</strong>'

    # Get the updated list of events
    events = stopwatch.get_events()
    event_list = '<br>'.join([
        f'<span style="color:{"green" if event_type.startswith("START") else "red" if event_type.startswith("Interval") else "blue"}">{event_type}: {timestamp}{f", Duration: {duration} seconds" if duration else ""}</span>'
        for timestamp, event_type, duration in events
    ])

    return render_template_string(template, status_message=status_message, message=message, event_list=event_list)

template = '''
<!DOCTYPE html>
<html>
<head>
    <title>Stopwatch</title>
</head>
<body>
    <h1>Stopwatch</h1>
    <form action="/" method="post">
        <button name="action" value="start">Start</button>
        <button name="action" value="stop">Stop</button>
        <button name="action" value="log_prompt">Log Prompt</button>
        <button name="action" value="reset">Reset</button>
        <button name="action" value="download_log">Download Log</button>
    </form>
    <div>{{ status_message|safe }}</div>
    <div>{{ message|safe }}</div>
    <div>{{ event_list|safe }}</div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
