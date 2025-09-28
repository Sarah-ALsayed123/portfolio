import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def shannon_entropy(proportions):
    proportions = [p for p in proportions if p > 0]
    if len(proportions) == 0:
        return 0
    return -sum(p * np.log2(p) for p in proportions)

# -------------------------------
def load_before():
    global data_before
    file_path = filedialog.askopenfilename(filetypes=[("Excel files","*.xlsx *.xls"),("CSV files","*.csv")])
    if file_path:
        if file_path.endswith('.csv'):
            data_before = pd.read_csv(file_path)
        else:
            data_before = pd.read_excel(file_path)
        before_status.config(text="✅ Loaded")

def load_after():
    global data_after
    file_path = filedialog.askopenfilename(filetypes=[("Excel files","*.xlsx *.xls"),("CSV files","*.csv")])
    if file_path:
        if file_path.endswith('.csv'):
            data_after = pd.read_csv(file_path)
        else:
            data_after = pd.read_excel(file_path)
        after_status.config(text="✅ Loaded")

def analyze():
    global canvas, delta_H, H_before, H_after, kill_message

    if 'data_before' not in globals() or 'data_after' not in globals():
        messagebox.showerror("Error", "Please load both Before and After files first.")
        return

    required_cols = ['Species','Proportion']
    for df, name in zip([data_before, data_after], ['Before','After']):
        if not all(col in df.columns for col in required_cols):
            messagebox.showerror("Error", f"Columns 'Species' and 'Proportion' required in {name} data.")
            return

    species = data_before['Species']
    before_prop = data_before['Proportion']
    after_prop = data_after['Proportion']

    H_before = shannon_entropy(before_prop)
    H_after = shannon_entropy(after_prop)
    delta_H = H_before - H_after

    kill_message = "No significant community death."
    if delta_H > 0.5:
        kill_message = "Significant community death detected!"

    # تحديث النصوص
    result_text.config(state='normal')
    result_text.delete('1.0', tk.END)
    result_text.insert(tk.END, f"Entropy Before: {H_before:.4f}\n"
                               f"Entropy After: {H_after:.4f}\n"
                               f"ΔH: {delta_H:.4f}\n"
                               f"{kill_message}\n")
    result_text.config(state='disabled')

    # الرسم البياني
    fig, ax = plt.subplots(figsize=(12, max(4,len(species)*0.5)))  # طول الرسم يعتمد على عدد الأنواع
    x = np.arange(len(species))
    width = 0.35
    ax.bar(x - width/2, before_prop, width, label='Before Antibiotic')
    ax.bar(x + width/2, after_prop, width, label='After Antibiotic')
    ax.set_xticks(x)
    ax.set_xticklabels(species, rotation=45, ha='right')
    ax.set_ylabel('Proportion')
    ax.set_title('Species Proportion Change After Antibiotic')
    ax.legend()
    plt.tight_layout()

    # إزالة الرسم القديم إذا موجود
    for widget in canvas_frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)

def save_results():
    if 'data_before' not in globals() or 'data_after' not in globals():
        messagebox.showerror("Error", "No analysis results to save.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Excel files","*.xlsx *.xls")],
                                             title="Save Analysis Results")
    if file_path:
        # حفظ بيانات الأنواع
        results_summary = pd.DataFrame({
            'Species': data_before['Species'],
            'Proportion_Before': data_before['Proportion'],
            'Proportion_After': data_after['Proportion']
        })
        # إنشاء Excel writer
        with pd.ExcelWriter(file_path) as writer:
            results_summary.to_excel(writer, sheet_name='Species Proportions', index=False)
            # حفظ معلومات التحليل في sheet آخر
            analysis_info = pd.DataFrame({
                'Parameter': ['Entropy Before','Entropy After','ΔH','Kill Message'],
                'Value': [H_before,H_after,delta_H,kill_message]
            })
            analysis_info.to_excel(writer, sheet_name='Analysis Summary', index=False)

        messagebox.showinfo("Saved", f"Results saved to '{file_path}'")

# -------------------------------
root = tk.Tk()
root.title("Microbial Community Entropy Analyzer")
root.geometry("990x630")

# أزرار التحميل والتحليل
frame = tk.Frame(root)
frame.pack(pady=10)

tk.Button(frame, text="Load Data Before Antibiotic", command=load_before, width=35).grid(row=0, column=0, pady=5)
before_status = tk.Label(frame, text="", fg="green", font=("Arial",12))
before_status.grid(row=0, column=1, padx=10)

tk.Button(frame, text="Load Data After Antibiotic", command=load_after, width=35).grid(row=1, column=0, pady=5)
after_status = tk.Label(frame, text="", fg="green", font=("Arial",12))
after_status.grid(row=1, column=1, padx=10)

tk.Button(frame, text="Analyze", command=analyze, width=35).grid(row=2, column=0, pady=5)
tk.Button(frame, text="Save Results", command=save_results, width=35).grid(row=3, column=0, pady=5)

# منطقة نصوص صغيرة
result_text = scrolledtext.ScrolledText(root, height=5, width=120, font=("Arial",12), state='disabled')
result_text.pack(pady=5)

# Frame للرسم البياني مع Scroll
canvas_container = tk.Frame(root)
canvas_container.pack(fill='both', expand=True)

canvas_scrollbar = tk.Scrollbar(canvas_container)
canvas_scrollbar.pack(side='right', fill='y')

canvas_frame = tk.Canvas(canvas_container, yscrollcommand=canvas_scrollbar.set)
canvas_frame.pack(side='left', fill='both', expand=True)

canvas_scrollbar.config(command=canvas_frame.yview)

# داخل canvas، سنضيف الرسم البياني عند التحليل
canvas_inner = tk.Frame(canvas_frame)
canvas_frame.create_window((0,0), window=canvas_inner, anchor='nw')

def on_frame_configure(event):
    canvas_frame.config(scrollregion=canvas_frame.bbox("all"))

canvas_inner.bind("<Configure>", on_frame_configure)

root.mainloop()




