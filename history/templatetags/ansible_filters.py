from django import template
import re
import html

register = template.Library()

@register.filter(name='format_ansible_output')
def format_ansible_output(text):
    """
    Formatea el output de Ansible con colores estilo terminal
    """
    if not text:
        return '<p class="text-muted">No output available</p>'
    
    # Escapar HTML para seguridad
    text = html.escape(text)
    
    # === Section headers ===
    text = re.sub(
        r'=== (.*?) ===',
        r'<span class="ansible-section-header">=== \1 ===</span>',
        text
    )
    
    # PLAY [...]
    text = re.sub(
        r'PLAY \[(.*?)\] \*+',
        r'<span class="ansible-play">PLAY [\1] ********************************</span>',
        text
    )
    
    # TASK [...]
    text = re.sub(
        r'TASK \[(.*?)\] \*+',
        r'<span class="ansible-task">TASK [<span class="ansible-task-name">\1</span>] ********************************</span>',
        text
    )
    
    # ok: [host]
    text = re.sub(
        r'ok: \[(.*?)\]',
        r'<span class="ansible-ok">ok: [\1]</span>',
        text
    )
    
    # changed: [host]
    text = re.sub(
        r'changed: \[(.*?)\]',
        r'<span class="ansible-changed">changed: [\1]</span>',
        text
    )
    
    # fatal: [host]
    text = re.sub(
        r'fatal: \[(.*?)\]',
        r'<span class="ansible-fatal">fatal: [\1]</span>',
        text
    )
    
    # PLAY RECAP
    text = re.sub(
        r'PLAY RECAP \*+',
        r'<span class="ansible-recap">PLAY RECAP ********************************</span>',
        text
    )
    
    # Statistics
    text = re.sub(r'\bok=(\d+)', r'<span class="ansible-stat-ok">ok=\1</span>', text)
    text = re.sub(r'\bchanged=(\d+)', r'<span class="ansible-stat-changed">changed=\1</span>', text)
    text = re.sub(r'\bfailed=(\d+)', r'<span class="ansible-stat-failed">failed=\1</span>', text)
    text = re.sub(r'\bunreachable=(\d+)', r'<span class="ansible-stat-unreachable">unreachable=\1</span>', text)
    text = re.sub(r'\bskipped=(\d+)', r'<span class="ansible-stat-skipped">skipped=\1</span>', text)
    
    # STDOUT/STDERR
    text = re.sub(
        r'^(STDOUT|STDERR):',
        r'<span class="ansible-output-label">\1:</span>',
        text,
        flags=re.MULTILINE
    )
    
    # cmd:, msg:, rc:
    text = re.sub(r'  cmd: (.+)', r'  <span class="ansible-cmd">cmd: \1</span>', text)
    text = re.sub(r'  msg: (.+)', r'<span class="ansible-msg">msg: \1</span>', text)
    text = re.sub(r'  rc: (\d+)', r'  <span class="ansible-stats">rc: \1</span>', text)
    
    # Checkmark
    text = re.sub(
        r'^✓ ',
        r'<span class="ansible-success-icon">✓ </span>',
        text,
        flags=re.MULTILINE
    )
    
    return text
