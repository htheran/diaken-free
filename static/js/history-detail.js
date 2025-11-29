/**
 * history-detail.js
 * Procesa y formatea la salida de Ansible con colores estilo terminal
 */

document.addEventListener('DOMContentLoaded', function() {
    const rawOutputContainer = document.querySelector('.ansible-raw-output');
    
    if (!rawOutputContainer) {
        console.warn('No se encontró el contenedor de salida de Ansible');
        return;
    }
    
    const rawOutput = rawOutputContainer.textContent;
    
    if (!rawOutput || rawOutput.trim() === '') {
        rawOutputContainer.style.display = 'block';
        rawOutputContainer.innerHTML = '<p class="text-muted">No output available</p>';
        return;
    }
    
    // Crear el contenedor formateado
    const formattedContainer = document.createElement('pre');
    formattedContainer.className = 'ansible-output';
    
    // Formatear el output
    const formattedOutput = formatAnsibleOutput(rawOutput);
    formattedContainer.innerHTML = formattedOutput;
    
    // Reemplazar el contenedor oculto con el formateado
    rawOutputContainer.parentNode.replaceChild(formattedContainer, rawOutputContainer);
});

function formatAnsibleOutput(text) {
    // Escapar HTML
    text = text.replace(/&/g, '&amp;')
               .replace(/</g, '&lt;')
               .replace(/>/g, '&gt;')
               .replace(/"/g, '&quot;')
               .replace(/'/g, '&#039;');
    
    // === Section headers ===
    text = text.replace(/=== (.*?) ===/g, '<span class="ansible-section-header">=== $1 ===</span>');
    
    // PLAY [...]
    text = text.replace(/PLAY \[(.*?)\] \*+/g, '<span class="ansible-play">PLAY [$1] ********************************</span>');
    
    // TASK [...]
    text = text.replace(/TASK \[(.*?)\] \*+/g, '<span class="ansible-task">TASK [<span class="ansible-task-name">$1</span>] ********************************</span>');
    
    // ok: [host]
    text = text.replace(/\bok: \[(.*?)\]/g, '<span class="ansible-ok">ok: [$1]</span>');
    
    // changed: [host]
    text = text.replace(/\bchanged: \[(.*?)\]/g, '<span class="ansible-changed">changed: [$1]</span>');
    
    // fatal: [host]
    text = text.replace(/\bfatal: \[(.*?)\]/g, '<span class="ansible-fatal">fatal: [$1]</span>');
    
    // skipping: [host]
    text = text.replace(/\bskipping: \[(.*?)\]/g, '<span class="ansible-skipping">skipping: [$1]</span>');
    
    // PLAY RECAP
    text = text.replace(/PLAY RECAP \*+/g, '<span class="ansible-recap">PLAY RECAP ********************************</span>');
    
    // Statistics
    text = text.replace(/\bok=(\d+)/g, '<span class="ansible-stat-ok">ok=$1</span>');
    text = text.replace(/\bchanged=(\d+)/g, '<span class="ansible-stat-changed">changed=$1</span>');
    text = text.replace(/\bfailed=(\d+)/g, '<span class="ansible-stat-failed">failed=$1</span>');
    text = text.replace(/\bunreachable=(\d+)/g, '<span class="ansible-stat-unreachable">unreachable=$1</span>');
    text = text.replace(/\bskipped=(\d+)/g, '<span class="ansible-stat-skipped">skipped=$1</span>');
    
    // STDOUT/STDERR
    text = text.replace(/^(STDOUT|STDERR):/gm, '<span class="ansible-output-label">$1:</span>');
    
    // cmd:, msg:, rc:
    text = text.replace(/  cmd: (.+)/g, '  <span class="ansible-cmd">cmd: $1</span>');
    text = text.replace(/  msg: (.+)/g, '  <span class="ansible-msg">msg: $1</span>');
    text = text.replace(/  rc: (\d+)/g, '  <span class="ansible-stats">rc: $1</span>');
    
    // Checkmark
    text = text.replace(/^✓ /gm, '<span class="ansible-success-icon">✓ </span>');
    
    // Warnings
    text = text.replace(/\[WARNING\]:?(.+)/g, '<span class="ansible-warning">[WARNING]:$1</span>');
    
    return text;
}
