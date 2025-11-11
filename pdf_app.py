import streamlit as st
import os, shutil, subprocess, time

st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """, unsafe_allow_html=True)
        
st.set_page_config(layout="wide")


cwd = os.path.dirname(__file__)
user_ip = st.context.ip_address
UPLOAD_DIR = os.path.join(cwd, 'uploads', user_ip) 
os.makedirs(UPLOAD_DIR, exist_ok=True)

outdir = os.path.join(UPLOAD_DIR, 'out') 
os.makedirs(outdir, exist_ok=True)
if "process" not in st.session_state:
    st.session_state.process = None
    
    
st.title("📄 PDF Highlighter - Upload Files")

import threading, time

def watchdog():
    while True:
        if st.session_state.get("last_interaction") and time.time() - st.session_state.last_interaction > 60:
            if st.session_state.process and st.session_state.process.poll() is None:
                st.session_state.process.terminate()
                st.session_state.process = None
            break
        time.sleep(5)

if "watchdog_started" not in st.session_state:
    st.session_state.watchdog_started = True



col1, col2 = st .columns([1,1])
with col1: 
    # Upload PDF
    pdf_file = st.file_uploader("Upload PDF", type="pdf")
    if pdf_file:
        pdf_path = os.path.join(UPLOAD_DIR, pdf_file.name)
        with open(pdf_path, "wb") as f:
            f.write(pdf_file.read())
        st.success(f"PDF saved at {pdf_path}")

    if st.button("Cancel Execution"):
        if st.session_state.process and st.session_state.process.poll() is None:
            st.session_state.process.terminate()
            st.session_state.process = None
            st.error("❌ Process terminated.")
with col2:
    option = st.radio("Choose BOM input:", ["Upload Excel", "Paste Text"])
    excel_path = None
    text_path = None    
    if option == "Upload Excel":
        excel_file = st.file_uploader("Upload Excel", type=["xlsx", "xls"])
        if excel_file:
            excel_path = os.path.join(UPLOAD_DIR, excel_file.name)
            with open(excel_path, "wb") as f:
                f.write(excel_file.read())
            st.success(f"Excel saved at {excel_path}")
    else:
        text_input = st.text_area("Paste text (comma-separated):", key= 'paste')
        if text_input.strip():
            text_path = os.path.join(UPLOAD_DIR, "input_text.txt")
            with open(text_path, "w") as f:
                f.write(text_input)
            st.success(f"Text saved at {text_path}")

def list_and_group(path2, ext_list) : #[ext1, ext2, ext3, ext4]):
    files = []
    for name in os.listdir(path2):
        if os.path.isfile(os.path.join(path2, name)):
            files.append(name)
    out_files = [None]*len(ext_list)
    for f in files:
        for idx,ext in enumerate(ext_list):
            if f.endswith(ext):
                out_files [idx] = f
                                
    return out_files
        
st.markdown("---")

col11, col21 = st .columns([1,1])
script1 = 'highlight_script.py'
s= list_and_group(UPLOAD_DIR, ['pdf','txt', 'xlsx'])



with col11:
    if st.button("Run Highlight script", key='b7'):
        if st.session_state.process and st.session_state.process.poll() is None:
            st.warning("A process is already running. Please stop it first.")
            st.stop()
        try:
            if s[0] == None:
                st.error('Upload pdf !!')
                st.stop()
            elif s[1] == None and s[2] != None:
                inp = s[2]
            elif s[1] != None and s[2] == None:
                inp = s[1]
            else:
                print ('-->', s)
                print (s[1] == None , s[1] != None)
                st.error('Upload excel or give some text input atleast')
                st.stop()
            
            pdf = os.path.join(UPLOAD_DIR, s[0])
            inp = os.path.join(UPLOAD_DIR, inp)
            output_path = os.path.join(UPLOAD_DIR, 'out' , s[0])
        #    result = subprocess.run(
        #        ["python", script1,\
        #            "--pdf", pdf   ,  \
        #            "--inp", inp   ,  \
        #            "--o"  , output_path  ,  \
        #            ],
        #        capture_output=True,
        #        text=True
        #    )
        
            cmd = ["python", script1,\
                    "--pdf", pdf   ,  \
                    "--inp", inp   ,  \
                    "--o"  , output_path  ,  \
                    ]
            st.session_state.process = process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            log_area = st.empty()
            progress_bar = st.progress(0)
            # log_area.text_area("Logs", value= "", height=300)

            st.write('started')
            logs = ""
            # for line in process.stdout:
            while True:
                if st.session_state.process.poll() is not None:
                    break
                line = st.session_state.process.stdout.readline()
                

                # Parse tqdm percentage if present
                if "%" in line:
                    # tqdm format: " 50%|█████     | 5/10 [00:01<00:01,  4.99it/s]"
                    try:
                        percent = int(line.split("%")[0].strip())
                        progress_bar.progress(percent)
                    except:
                        pass
                else:
                    logs += line
                    # log_area.value = logs
                    log_area.text_area("Logs", value= logs, height=300)

                time.sleep(0.05)  # Allow UI refresh

            st.success("✅ Script completed!")

            if os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Processed PDF",
                        data=f,
                        file_name="highlighted-"+s[0],
                        mime="application/pdf"
                    )
            else:
                st.warning("Processed file not found. Please run the processing first.")
            
            
        except Exception as e:
            st.error(f"Error running script: {e}")

    
with col21:

            
            
    if st.button("Clean Uploads Folder"):
        if os.path.exists(UPLOAD_DIR):
            try:
                shutil.rmtree(UPLOAD_DIR)
                os.makedirs(UPLOAD_DIR, exist_ok=True)  # Recreate empty folder
                st.success("✅ Uploads folder cleaned successfully.")
            except Exception as e:
                st.error(f"❌ Error cleaning uploads folder: {e}")
        else:
            st.warning("⚠ Uploads folder does not exist.")
    st.write(s)
    

    # else:
        # st.warning("No process running.")
