// js/files.js : gestion des fichiers à traduire, drag & drop, affichage liste fichiers

function setupFileHandlers() {
    const fileUpload = document.getElementById('fileUpload');
    const fileInput = document.getElementById('fileInput');
    fileUpload.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    fileUpload.addEventListener('dragover', (e) => {
        e.preventDefault();
        fileUpload.classList.add('dragover');
    });
    fileUpload.addEventListener('dragleave', () => {
        fileUpload.classList.remove('dragover');
    });
    fileUpload.addEventListener('drop', (e) => {
        e.preventDefault();
        fileUpload.classList.remove('dragover');
        handleFileDrop(e);
    });
}

function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    addFiles(files);
}

function handleFileDrop(event) {
    const files = Array.from(event.dataTransfer.files);
    addFiles(files);
}

function addFiles(files) {
    files.forEach(file => {
        if (!selectedFiles.find(f => f.name === file.name && f.size === file.size)) {
            selectedFiles.push(file);
        }
    });
    updateFileList();
    updateTranslateButton();
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateTranslateButton();
}

function updateFileList() {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        const fileName = document.createElement('div');
        fileName.className = 'file-item-name';
        fileName.textContent = file.name;
        const fileSize = document.createElement('div');
        fileSize.className = 'file-item-size';
        fileSize.textContent = formatFileSize(file.size);
        const removeBtn = document.createElement('button');
        removeBtn.className = 'file-remove';
        removeBtn.textContent = '×';
        removeBtn.onclick = () => removeFile(index);
        fileItem.appendChild(fileName);
        fileItem.appendChild(fileSize);
        fileItem.appendChild(removeBtn);
        fileList.appendChild(fileItem);
    });
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}
