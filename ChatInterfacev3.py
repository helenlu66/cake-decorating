import tkinter as tk
import threading
from tkinter import font
from datetime import datetime
from tkinter import simpledialog
from ConfigUtil import load_experiment_config
from ChatAgent import ChatAgent

class ChatInterface:
    def __init__(self, root):
        # Define a larger font
        self.custom_font = font.Font(family="Helvetica", size=14)

        # Setting up the chat area with a larger font
        self.chat_area = tk.Text(root, state='disabled', wrap='word', font=self.custom_font)
        self.chat_area.pack(padx=10, pady=10, expand=True, fill='both')

        # Setting up the user input area with larger font
        self.user_input_area = tk.Entry(root, font=self.custom_font)
        self.user_input_area.pack(padx=10, pady=10, fill='x')
        self.user_input_area.bind("<Return>", self.handle_user_input)

        self.root = root
        self.root.title(exp_config["exp_chat_interface_title"])
        self.welcome_message = f"Hello {exp_config['user_name']}, let's decorate a cake together. What would you like me to do first?"
        self.goodbye_message = "Goodbye! Have a nice day!"


        # logging
        # Open or create a log file for this session
        self.log_file = open(f"experiment_log/{exp_config['user_name']}_{exp_config['exp_condition']}.log", "a")

        self.robot_response_enabled = exp_config['exp_condition'].lower() != 'base'
        self.chat = ChatAgent()
        self.prepared_response = "something went wrong"
        self.response_received =False
        self.initialize_chat()


    def get_text_response(self, user_input):
        response = self.chat.process_human_input(user_input)
        return response

    def handle_user_input(self, event=None):
        
        user_input = self.user_input_area.get()
        self.append_message(user_input, "You")
        self.user_input_area.delete(0, tk.END)
        if user_input.lower() == 'done':
            if self.robot_response_enabled:
                self.append_message(self.goodbye_message, "Robot")
            else:
                self.append_message(self.goodbye_message)
            self.root.after(2000, self.root.destroy)  # Wait 2 seconds before closing
        else:
            self.user_input_area.delete(0, tk.END)
            self.response_received = False
            threading.Thread(target=self.process_user_input, args=(user_input,), daemon=True).start()
            self.display_processing_message()

    def display_processing_message(self):
        self.append_message("The robot is processing your message...")
        self.processing_message_id = self.chat_area.index(tk.END)
        self.update_processing_message()

    def update_processing_message(self, count=1):
        if self.response_received:
            return
        if count > 3:
            count = 1
        print("generating .")
       
        self.chat_area.config(state='normal')
        self.chat_area.delete(self.processing_message_id, tk.END)
        self.chat_area.insert(self.processing_message_id, "."*count + "\n")
        self.chat_area.config(state='disabled')
        self.chat_area.see(tk.END)
        if not hasattr(self, 'response_received') or not self.response_received:
            self.root.after(1000, self.update_processing_message,  count + 1)

    def process_user_input(self, user_input):
        self.response_received = False
        response = self.get_text_response(user_input)  # Simulate long-running task
        self.response_received = True
        if self.robot_response_enabled:
            self.append_message(response, "Robot")
        else:
            self.append_message(response)


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
