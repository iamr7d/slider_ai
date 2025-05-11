const fs = require('fs');

const filePath = 'c:/Users/rahul/OneDrive/Desktop/SLIDE.AI/webapp-frontend/src/components/KonvaTextToolbar.jsx';

// Read the file
let content = fs.readFileSync(filePath, 'utf8');

// Find the position of the second colors declaration
const firstDeclaration = content.indexOf('const colors = isDarkMode ?');
const secondDeclaration = content.indexOf('const colors = isDarkMode ?', firstDeclaration + 1);

if (secondDeclaration !== -1) {
  // Find the end of the second colors object (the closing semicolon after the object)
  const endOfObject = content.indexOf('};', secondDeclaration);
  
  if (endOfObject !== -1) {
    // Replace the entire second colors declaration with a comment
    const beforeSecondDeclaration = content.substring(0, secondDeclaration);
    const afterSecondDeclaration = content.substring(endOfObject + 2); // +2 to include the };
    
    // Create the new content with the second declaration commented out
    const newContent = beforeSecondDeclaration + 
      '// Using the colors object defined earlier in the component' + 
      afterSecondDeclaration;
    
    // Write the modified content back to the file
    fs.writeFileSync(filePath, newContent);
    
    console.log('File updated successfully!');
  } else {
    console.error('Could not find the end of the second colors object');
  }
} else {
  console.log('No duplicate colors declaration found');
}
