// Позволяет колонке принимать элемент
function allowDrop(event) {
    event.preventDefault();
}

// Инициализация перетаскивания
function drag(event) {
    event.dataTransfer.setData("text", event.target.id);
}
