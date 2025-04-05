from tkinter import Tk, Frame, Label, Entry, Button, filedialog
from Domain import Domain

root = Tk()


def verify_smells(path,destiny):
    path_file = path.replace('/','\\')
    Domain(path_file=path_file)


class Aplication(): 
    def __init__(self):
        self.root = root
        self.screen()
        self.frame_screen()
        self.widgets()
        self.root.mainloop()

    def screen(self):
        self.root.title("Agnose")
        self.root.configure(background="black")
        self.root.geometry("700x500")
        self.root.resizable(True,True)
        self.root.maxsize(width=900, height=600)
        self.root.minsize(width=400, height=300)

    def frame_screen(self):
        self.frame_1 = Frame(self.root, bd=2, bg="blue", highlightbackground="pink", highlightthickness=2)
        self.frame_1.place(relx=0.1,rely=0.04, relwidth = 0.8, relheight = 0.25)

        self.frame_2 = Frame(self.root, bd=2, bg="blue", highlightbackground="pink", highlightthickness=2)
        self.frame_2.place(relx=0.1,rely=0.5, relwidth = 0.3, relheight = 0.45)

        # self.frame_3= Frame(self.root, bd=2, bg="blue", highlightbackground="pink", highlightthickness=2)
        # self.frame_3.place(relx=0.1,rely=0.1, relwidth = 0.8, relheight = 0.5)

    def widgets(self):

        lb_path = Label(self.frame_1,text="Caminho do código: ")
        lb_path.place(relx=0.04, rely=0.15, relwidth=0.21, relheight=0.20 )
        

        path_dir = ''
        path_entry = Label(self.frame_1, text=path_dir)
        path_entry.place(relx=0.25, rely=0.15, relwidth=0.6, relheight=0.20)

        search_path = Button(self.frame_1, text="Search", command=lambda:self.open_dir(directory=path_dir, label=path_entry))
        search_path.place(relx=0.85,rely=0.15, relwidth=0.1, relheight=0.20)


        lb_destiny = Label(self.frame_1,text="Destino CSV: ")
        lb_destiny.place(relx=0.04, rely=0.39, relwidth=0.21, relheight=0.20 )

        destiny_dir = ''
        destiny_entry = Label(self.frame_1, text=destiny_dir)
        destiny_entry.place(relx=0.25, rely=0.39, relwidth=0.6, relheight=0.20 )

        search_destiny = Button(self.frame_1, text="Search", command=lambda:self.open_dir(directory=destiny_dir, label=destiny_entry))
        search_destiny.place(relx=0.85,rely=0.39, relwidth=0.1, relheight=0.20)


        create_button = Button(self.frame_1, text="Verificar Smells", font=0.5, command=lambda:verify_smells(path= path_entry.cget("text"),destiny= destiny_entry.cget("text") ))
        create_button.place(relx=0.35,rely=0.7, relwidth=0.3, relheight=0.22)


        lb_console= Label(self.frame_2,text="Console")
        lb_console.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.15 )

    def open_dir(self, directory, label):
        directory = filedialog.askdirectory()
        label.config(text=directory)
        print(label.cget("text"))
        


Aplication()