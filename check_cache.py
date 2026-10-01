"""Session-local reuse; one complete result per check, invalidated by input hash."""
import streamlit as st
import design_basis

def get_or_compute(name,inputs,compute):
    key=design_basis.fingerprint(inputs)
    cache=st.session_state.setdefault('checks_cache',{})
    old=cache.get(name)
    if old and old[0]==key:return old[1]
    result=compute() # A failed computation never replaces a complete entry.
    cache[name]=(key,result)
    return result
