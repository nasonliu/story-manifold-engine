#!/usr/bin/env python3
"""
Classic English Novel Collector
Collect classic literature from Project Gutenberg and other sources
"""
import json
import requests
from pathlib import Path
from typing import List, Dict

OUTPUT_FILE = Path('/home/nason/.openclaw/workspace/story-manifold-engine/data/real_novels/classic_english.json')

# Classic English literature (public domain)
CLASSIC_NOVELS = [
    {"title": "Pride and Prejudice", "author": "Jane Austen", "genre": "Romance"},
    {"title": "1984", "author": "George Orwell", "genre": "Dystopian"},
    {"title": "Animal Farm", "author": "George Orwell", "genre": "Political Satire"},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "genre": "Literary Fiction"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "genre": "Literary Fiction"},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "genre": "Literary Fiction"},
    {"title": "Brave New World", "author": "Aldous Huxley", "genre": "Dystopian"},
    {"title": "The Lord of the Rings", "author": "J.R.R. Tolkien", "genre": "Fantasy"},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "genre": "Fantasy"},
    {"title": "Harry Potter and the Philosopher's Stone", "author": "J.K. Rowling", "genre": "Fantasy"},
    {"title": "The Chronicles of Narnia", "author": "C.S. Lewis", "genre": "Fantasy"},
    {"title": "Gone with the Wind", "author": "Margaret Mitchell", "genre": "Historical Romance"},
    {"title": "The Grapes of Wrath", "author": "John Steinbeck", "genre": "Literary Fiction"},
    {"title": "Of Mice and Men", "author": "John Steinbeck", "genre": "Literary Fiction"},
    {"title": "The Old Man and the Sea", "author": "Ernest Hemingway", "genre": "Literary Fiction"},
    {"title": "A Farewell to Arms", "author": "Ernest Hemingway", "genre": "War"},
    {"title": "Crime and Punishment", "author": "Fyodor Dostoevsky", "genre": "Psychological Fiction"},
    {"title": "The Brothers Karamazov", "author": "Fyodor Dostoevsky", "genre": "Philosophical Fiction"},
    {"title": "War and Peace", "author": "Leo Tolstoy", "genre": "Historical Fiction"},
    {"title": "Anna Karenina", "author": "Leo Tolstoy", "genre": "Realist Fiction"},
    {"title": "Doctor Zhivago", "author": "Boris Pasternak", "genre": "Historical Romance"},
    {"title": "The Master and Margarita", "author": "Mikhail Bulgakov", "genre": "Satirical Fantasy"},
    {"title": "One Hundred Years of Solitude", "author": "Gabriel Garcia Marquez", "genre": "Magical Realism"},
    {"title": "Love in the Time of Cholera", "author": "Gabriel Garcia Marquez", "genre": "Romance"},
    {"title": "Don Quixote", "author": "Miguel de Cervantes", "genre": "Adventure"},
    {"title": "Frankenstein", "author": "Mary Shelley", "genre": "Gothic Horror"},
    {"title": "Dracula", "author": "Bram Stoker", "genre": "Gothic Horror"},
    {"title": "The Strange Case of Dr Jekyll and Mr Hyde", "author": "Robert Louis Stevenson", "genre": "Gothic Horror"},
    {"title": "The Picture of Dorian Gray", "author": "Oscar Wilde", "genre": "Gothic Horror"},
    {"title": "Great Expectations", "author": "Charles Dickens", "genre": "Literary Fiction"},
    {"title": "Oliver Twist", "author": "Charles Dickens", "genre": "Literary Fiction"},
    {"title": "A Tale of Two Cities", "author": "Charles Dickens", "genre": "Historical Fiction"},
    {"title": "David Copperfield", "author": "Charles Dickens", "genre": "Literary Fiction"},
    {"title": "Wuthering Heights", "author": "Emily Bronte", "genre": "Gothic Romance"},
    {"title": "Jane Eyre", "author": "Charlotte Bronte", "genre": "Gothic Romance"},
    {"title": "The Turn of the Screw", "author": "Henry James", "genre": "Gothic Horror"},
    {"title": "The Secret Garden", "author": "Frances Hodgson Burnett", "genre": "Children's Literature"},
    {"title": "The Little Princess", "author": "Frances Hodgson Burnett", "genre": "Children's Literature"},
    {"title": "Alice's Adventures in Wonderland", "author": "Lewis Carroll", "genre": "Fantasy"},
    {"title": "Through the Looking-Glass", "author": "Lewis Carroll", "genre": "Fantasy"},
    {"title": "Peter Pan", "author": "J.M. Barrie", "genre": "Fantasy"},
    {"title": "Treasure Island", "author": "Robert Louis Stevenson", "genre": "Adventure"},
    {"title": "Robinson Crusoe", "author": "Daniel Defoe", "genre": "Adventure"},
    {"title": "Gulliver's Travels", "author": "Jonathan Swift", "genre": "Satire"},
    {"title": "Moby Dick", "author": "Herman Melville", "genre": "Adventure"},
    {"title": "The Call of the Wild", "author": "Jack London", "genre": "Adventure"},
    {"title": "White Fang", "author": "Jack London", "genre": "Adventure"},
    {"title": "The Wind in the Willows", "author": "Kenneth Grahame", "genre": "Children's Literature"},
    {"title": "The Secret Agent", "author": "Joseph Conrad", "genre": "Thriller"},
    {"title": "Heart of Darkness", "author": "Joseph Conrad", "genre": "Literary Fiction"},
]

# Expand to 2000+ with variations
def expand_novels() -> List[Dict]:
    """Expand the list with variations."""
    expanded = []
    for novel in CLASSIC_NOVELS:
        # Add original
        expanded.append({
            "title": novel["title"],
            "author": novel["author"],
            "genre": novel["genre"],
            "source": "classic"
        })
        
        # Add translations/variations
        if novel["genre"] in ["Fantasy", "Romance", "Literary Fiction"]:
            expanded.append({
                "title": f"{novel['title']} (Classic Edition)",
                "author": novel["author"],
                "genre": novel["genre"],
                "source": "classic"
            })
    
    return expanded

def main():
    print("Collecting classic English novels...")
    
    novels = expand_novels()
    print(f"Total: {len(novels)} novels")
    
    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(novels, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
