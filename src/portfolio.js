import './style.css';
import { PROJECTS } from './projects.js';

const list = document.querySelector('.portfolio-list');
for (const project of PROJECTS) {
  const item = document.createElement('li');
  const link = document.createElement('a');
  link.href = project.url;
  link.target = '_blank';
  link.rel = 'noopener';

  const name = document.createElement('strong');
  name.textContent = project.name;
  const note = document.createElement('span');
  note.textContent = project.note;
  link.append(name, note);
  item.append(link);
  list.append(item);
}

for (const link of document.querySelectorAll('[data-project]')) {
  link.href = PROJECTS.find((project) => project.id === link.dataset.project).url;
}

document.getElementById('contacts-panel').append(document.querySelector('.final .links').cloneNode(true));

for (const button of document.querySelectorAll('[data-dialog]')) {
  const dialog = document.getElementById(button.dataset.dialog);
  button.addEventListener('click', () => dialog.showModal());
}
