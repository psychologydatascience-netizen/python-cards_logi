import streamlit as st
import pandas as pd
import random
import time

# Function to load trials from Excel
@st.cache_data
def load_trials_from_excel(filepath):
    df = pd.read_excel(filepath)
    
    trials = []
    current_trial = {}
    
    for idx, row in df.iterrows():
        card_type = row['type']
        code = str(row['code'])
        card_path = f"cards/{code}.png"
        features = str(row['features']) if 'features' in row else ""
        
        if card_type == 'main':
            # If we already have a trial being built, save it
            if current_trial:
                trials.append(current_trial)
            # Start new trial
            current_trial = {
                'main': card_path,
                'main_features': set(features),  # Convert to set for easy comparison
                'correct_card': None,
                'correct_features': None,
                'cards_data': []  # Store all option cards with their features
            }
        elif card_type == 'correct':
            current_trial['correct_card'] = card_path
            current_trial['correct_features'] = set(features)
            current_trial['cards_data'].append({
                'path': card_path,
                'features': set(features),
                'is_correct': True
            })
        elif card_type.startswith('wr_'):
            current_trial['cards_data'].append({
                'path': card_path,
                'features': set(features),
                'is_correct': False
            })
    
    # Don't forget the last trial
    if current_trial:
        trials.append(current_trial)
    
    # Now randomize the position of cards in each trial
    for trial in trials:
        # Shuffle the cards
        random.shuffle(trial['cards_data'])
        
        # Find where the correct card ended up
        correct_index = next(i for i, card in enumerate(trial['cards_data']) 
                            if card['is_correct'])
        
        # Store in trial data
        trial['options'] = [card['path'] for card in trial['cards_data']]
        trial['correct'] = correct_index
    
    return trials

# Function to check if answer is half correct
def check_answer(trial_data, selected_index):
    correct_features = trial_data['cards_data'][trial_data['correct']]['features']
    selected_features = trial_data['cards_data'][selected_index]['features']
    
    if selected_index == trial_data['correct']:
        return "correct"
    
    # Check how many features match
    matching_features = correct_features & selected_features  # Set intersection
    
    if len(matching_features) >= 1:  # At least one feature matches
        return "half_correct"
    else:
        return "incorrect"

# Load trials from Excel
try:
    TRIALS = load_trials_from_excel("cards_codes.xlsx")
except FileNotFoundError:
    st.error("❌ Could not find 'cards_codes.xlsx'. Please make sure the file exists.")
    st.stop()
except Exception as e:
    st.error(f"❌ Error loading Excel file: {e}")
    st.stop()

# Initialize session state
if "trial" not in st.session_state:
    st.session_state.trial = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "feedback" not in st.session_state:
    st.session_state.feedback = None  # "correct", "half_correct", or "incorrect"
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False

# End screen
if st.session_state.trial >= len(TRIALS):
    st.title("Done 🎉")
    st.write(f"Final score: {st.session_state.score} / {len(TRIALS)}")
    if st.button("Restart"):
        st.session_state.trial = 0
        st.session_state.score = 0
        st.session_state.feedback = None
        st.session_state.show_feedback = False
    st.stop()

# Normal trial display
trial_data = TRIALS[st.session_state.trial]
st.title(f"Trial {st.session_state.trial + 1}")

# Display main card
st.image(trial_data["main"], width=260)

# Show feedback prominently near the main card
if st.session_state.show_feedback:
    if st.session_state.feedback == "correct":
        st.success("# ✅ Correct!", icon="✅")
    elif st.session_state.feedback == "half_correct":
        st.warning("# 🟡 Close! One feature matches", icon="⚠️")
    else:
        st.error("# ❌ Incorrect", icon="❌")
    
    # Pause briefly, then move on
    time.sleep(1.2)
    # Advance to next trial
    st.session_state.trial += 1
    st.session_state.feedback = None
    st.session_state.show_feedback = False
    st.rerun()

st.write("### Choose a card:")

cols = st.columns(4)
for i, col in enumerate(cols):
    with col:
        st.image(trial_data["options"][i], width=120)
        if st.button(f"Select", key=f"opt_{st.session_state.trial}_{i}"):
            feedback_type = check_answer(trial_data, i)
            
            if feedback_type == "correct":
                st.session_state.score += 1
            
            st.session_state.feedback = feedback_type
            st.session_state.show_feedback = True
            st.rerun()