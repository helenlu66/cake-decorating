import tkinter as tk
from datetime import datetime
from tkinter import simpledialog
from ConfigUtil import load_experiment_config

class ChatInterface:
    def __init__(self, root):
        self.root = root
        self.root.title(exp_config["exp_chat_interface_title"])
        self.welcome_message = f"Hello {exp_config['user_name']}, let's decorate a cake together. "
        self.goodbye_message = "Goodbye! Have a nice day!"

        # Setting up the chat area
        self.chat_area = tk.Text(root, state='disabled', wrap='word')
        self.chat_area.pack(padx=10, pady=10, expand=True, fill='both')

        # Setting up the user input area
        self.user_input_area = tk.Entry(root)
        self.user_input_area.pack(padx=10, pady=10, fill='x')
        self.user_input_area.bind("<Return>", self.handle_user_input)

        # logging
        # Open or create a log file for this session
        self.log_file = open(f"experiment_log/{exp_config['user_name']}_{exp_config['exp_condition']}.log", "a")

        self.robot_response_enabled = exp_config['exp_condition'] != 'base'
        self.initialize_chat()


    def get_text_response(self, user_input):
        # Implement your AI logic here. For now, it just echoes the user input
        return f"You said: {user_input}"

    def handle_user_input(self, event=None):
        user_input = self.user_input_area.get()
        if user_input.lower() == 'done':
            self.append_message(self.goodbye_message, "Robot")
            self.root.after(2000, self.root.destroy)  # Wait 2 seconds before closing
        else:
            self.append_message(user_input, "You")
            self.user_input_area.delete(0, tk.END)
            # handle the action if there's any
            # Get the AI response immediately, but don't display it yet
            self.prepared_response = self.get_text_response(user_input)
            # Show typing indicator on a new line
            self.typing_indicator_id = self.chat_area.index(tk.END)
            self.append_message("The robot is processing your message ...")
            # self.chat_area.config(state='normal')
            # self.chat_area.insert(tk.END, "The robot is processing your message ...\n")
            # self.chat_area.config(state='disabled')
            self.update_typing_indicator(repetitions=exp_config['wait_for_action_completion'])
    

    def update_typing_indicator(self, repetitions):
        if repetitions > 0:
            current_text = self.chat_area.get(self.typing_indicator_id, tk.END)
            # Append one dot to the typing indicator
            new_text = current_text.strip() + '.'
            # Replace the last line with the updated typing indicator
            self.chat_area.config(state='normal')
            self.chat_area.delete(self.typing_indicator_id, tk.END)
            self.chat_area.insert(self.typing_indicator_id, new_text + "\n")
            self.chat_area.config(state='disabled')
            # Schedule the next update
            self.root.after(1000, self.update_typing_indicator, repetitions - 1)
        else:
            # After the last repetition, append the next message
            self.respond()

    def respond(self):
        # Remove typing indicator before showing the response
        self.chat_area.config(state='normal')
        self.chat_area.delete(self.typing_indicator_id, tk.END)
        # Ensure the next message starts on a new line
        if not self.chat_area.get('1.0', tk.END).endswith('\n'):
            self.chat_area.insert(tk.END, "\n")
        self.chat_area.config(state='disabled')
        if self.robot_response_enabled:
            self.append_message(self.prepared_response, "Robot")
        else:
            #TODO:get a default response for the base condition
            self.append_message(self.report_system_status())

    
    def report_system_status(self):
        #TODO:generate system status message
        return "system status"

    def append_message(self, message, sender=None):
        self.chat_area.config(state='normal')
        # Ensure the message starts on a new line if the chat area is not empty
        if not self.chat_area.get('1.0', tk.END).strip().endswith('\n'):
            self.chat_area.insert(tk.END, "\n")
        if sender:
            formatted_message = f"{sender}: {message}\n"
        else:
            formatted_message = f"{message}\n"
        self.chat_area.insert(tk.END, formatted_message)
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)

        # Write message to log file with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_file.write(f"{timestamp} - {sender if sender else 'System'}: {message}\n")
        self.log_file.flush()


    def initialize_chat(self):
        if self.robot_response_enabled:
            self.append_message(exp_config['exp_welcome_message'])
            self.append_message(self.welcome_message, "Robot")
        else:
            self.append_message(exp_config['exp_welcome_message'])
    

    def __del__(self):
        # Close the log file when the ChatAgent object is destroyed
        if self.log_file:
            self.log_file.close()

if __name__ == "__main__":
    exp_config = load_experiment_config('experiment_config.yaml')
    root = tk.Tk()
    agent = ChatInterface(root)
    root.mainloop()
