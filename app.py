# app.py

import gradio as gr
from env.environment import CodeDebugEnv

# Sample task (you can later load dynamically)
task = {
    "buggy_code": "def add(a,b):\n    return a-b",
    "tests": [
        {"function": "add", "input": [2, 3], "expected": 5}
    ]
}

env = CodeDebugEnv(task)
state, _ = env.reset()


def run_step(action_type, line):
    global state

    action = (action_type, line)
    state, reward, terminated, truncated, info = env.step(action)

    return state.tolist(), reward, info, terminated or truncated


with gr.Blocks() as demo:
    gr.Markdown("# Code Debug RL Environment")

    action_type = gr.Slider(0, 2, step=1, label="Action Type (0=replace,1=delete,2=insert)")
    line = gr.Slider(0, 10, step=1, label="Line Number")

    state_out = gr.Textbox(label="Encoded State")
    reward_out = gr.Number(label="Reward")
    info_out = gr.JSON(label="Info")
    done_out = gr.Textbox(label="Done")

    btn = gr.Button("Step")

    btn.click(
        run_step,
        inputs=[action_type, line],
        outputs=[state_out, reward_out, info_out, done_out]
    )

demo.launch()
