const { Translator, Credentials } = require('@translated/lara');

console.log('Inspecting Lara SDK...');

try {
    const credentials = new Credentials('test', 'test');
    const lara = new Translator(credentials);

    console.log('Translator keys:', Object.keys(lara));
    
    if (lara.glossaries) {
        console.log('Glossaries object found');
        console.log('Glossaries prototype:', Object.getPrototypeOf(lara.glossaries));
        console.log('Glossaries keys:', Object.keys(lara.glossaries));
        
        // Check for methods on the prototype
        const proto = Object.getPrototypeOf(lara.glossaries);
        console.log('Glossaries methods:', Object.getOwnPropertyNames(proto));
    } else {
        console.log('Glossaries object NOT found on Translator instance');
    }

} catch (error) {
    console.error('Error inspecting SDK:', error);
}
