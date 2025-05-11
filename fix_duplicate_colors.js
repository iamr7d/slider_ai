const fs = require('fs');

const filePath = 'c:/Users/rahul/OneDrive/Desktop/SLIDE.AI/webapp-frontend/src/components/KonvaTextToolbar.jsx';

// Read the file
let content = fs.readFileSync(filePath, 'utf8');

// Split the content into lines
const lines = content.split('\n');

// Find the line numbers of the colors declarations
const colorDeclarationLines = [];
lines.forEach((line, index) => {
  if (line.trim().startsWith('const colors =')) {
    colorDeclarationLines.push(index);
  }
});

console.log('Found colors declarations at lines:', colorDeclarationLines);

// If we found more than one declaration, comment out the second one
if (colorDeclarationLines.length > 1) {
  const secondDeclarationLine = colorDeclarationLines[1];
  
  // Comment out the second declaration and the entire object
  lines[secondDeclarationLine] = '  // Using the colors object defined earlier in the component';
  
  // Find the end of the object (the closing brace and semicolon)
  let endLine = secondDeclarationLine + 1;
  while (endLine < lines.length && !lines[endLine].includes('};')) {
    lines[endLine] = '  // ' + lines[endLine];
    endLine++;
  }
  
  if (endLine < lines.length) {
    lines[endLine] = '  // ' + lines[endLine];
  }
  
  // Write the modified content back to the file
  fs.writeFileSync(filePath, lines.join('\n'));
  
  console.log('Successfully commented out the duplicate colors declaration');
} else {
  console.log('No duplicate colors declaration found');
}
