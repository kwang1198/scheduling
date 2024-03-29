import sys
sys.path.insert(0, 'src')
sys.path.insert(0, './')
import argparse
from platforms.app import App
from converter import converter

parser = argparse.ArgumentParser()
parser.add_argument('--input', '-i', default='samples/size/sample.15.json')
args = parser.parse_args()

app = App()
dag_like = converter(args.input)
app.read_input(dag_like, format='mb')

_, min_makespan, max_usage = app.schedule('heft')
print(min_makespan, max_usage)

# _, makespan, usage = app.schedule('heft_delay', 150)
# print(makespan, usage)

# _, makespan, usage = app.schedule('heft_lookup', 150, {'depth': 1})
# print(makespan, usage)