# Basic RAG using Lexy

## Introduction

Let's go through a basic implementation of Retrieval Augmented Generation (RAG) using Lexy. RAG is the process of using a retriever to find relevant documents to include in the prompt as context for a language model. 

In this example, we'll use Lexy to store and retrieve documents describing characters from the TV show House of the Dragon. We'll then use those documents to construct a prompt that GPT-4 can use to answer questions about the characters.

### OpenAI API Key

Note that this example requires an OpenAI API key. You can add your API key as an environment variable using the `.env` file in the root directory of the Lexy repository. See [How do I add a new environment variable](../faq.md#how-do-i-add-a-new-environment-variable) on the [FAQ page](../faq.md) for more details.

```shell title=".env"
OPENAI_API_KEY=your_secret_api_key
```

Remember to rebuild your containers after adding the environment variable. Simply run the following on the command line.

```shell
make update-dev-containers
```

## Sample data

Our data is in the `sample_data/documents` directory. Let's import it and take a look at the first few lines. 


```python
with open("../sample_data/documents/hotd.txt") as f:
    lines = f.read().splitlines()
    
lines[:3]
```



```{ .text .no-copy .result #code-output }
['Viserys I Targaryen is the fifth king of the Targaryen dynasty to rule the Seven Kingdoms. He is the father of Rhaenyra Targaryen and Aegon II Targaryen. His mount is the dragon Balerion.',
 'Rhaenyra Targaryen is the eldest child of King Viserys I Targaryen and is considered the heir to the Iron Throne. She is a dragonrider whose mount is Syrax.',
 'Aegon II Targaryen is the second-born child of Viserys I Targaryen and Alicent Hightower. He is a claimant to the Iron Throne and a dragonrider whose mount is Sunfyre.']
```


## Add documents to Lexy

Now let's instantiate a Lexy client and create a new collection for our documents.


```python
from lexy_py import LexyClient

lexy = LexyClient()

# create a new collection
collection = lexy.create_collection(
    collection_id="house_of_the_dragon", 
    description="House of the Dragon characters"
)
collection
```



```{ .text .no-copy .result #code-output }
<Collection('house_of_the_dragon', description='House of the Dragon characters')>
```


We can add documents to our new collection using the `add_documents` method.


```python
collection.add_documents([
    {"content": line} for line in lines
])
```



```{ .text .no-copy .result #code-output }
[<Document("Viserys I Targaryen is the fifth king of the Targaryen dynasty to rule the Seven Kingdoms. He is...")>,
 <Document("Rhaenyra Targaryen is the eldest child of King Viserys I Targaryen and is considered the heir to...")>,
 <Document("Aegon II Targaryen is the second-born child of Viserys I Targaryen and Alicent Hightower. He is a...")>,
 <Document("Daemon Targaryen is the younger brother of King Viserys I Targaryen, and is the heir to the...")>,
 <Document("Aemond Targaryen is the second son of King Viserys I Targaryen and Alicent Hightower. He is a...")>,
 <Document("Alicent Hightower is the Queen of the Seven Kingdoms and the mother of Aegon II Targaryen, the...")>,
 <Document("Otto Hightower is the Hand of the King to Viserys I Targaryen and the father of Alicent...")>,
 <Document("Laena Velaryon is a dragonrider and the wife of Daemon Targaryen. Her mount is the dragon Vhagar.")>,
 <Document("Corlys Velaryon, also known as the Sea Snake, is the Lord of the Tides and head of House...")>,
 <Document("Rhaenys Targaryen, also known as the Queen Who Never Was, is a dragonrider and the wife of Corlys...")>,
 <Document("Syrax is the dragon ridden by Rhaenyra Targaryen. She is known for her golden scales and fierce...")>,
 <Document("Vhagar is one of the oldest and largest dragons, originally ridden by Visenya Targaryen. She...")>,
 <Document("Sunfyre is a dragon known for his magnificent golden scales and is the mount of Aegon II Targaryen.")>,
 <Document("Meleys, also known as the Red Queen, is the dragon ridden by Rhaenys Targaryen. She is known for...")>,
 <Document("Seasmoke is a dragon ridden by Laenor Velaryon, son of Corlys Velaryon and Rhaenys Targaryen. He...")>,
 <Document("Vermax is a dragon ridden by Jacaerys Velaryon, the eldest son of Rhaenyra Targaryen. He is known...")>,
 <Document("Balerion, also known as the Black Dread, was the largest of the Targaryen dragons. He was ridden...")>,
 <Document("Caraxes, also known as the Blood Wyrm, is the dragon ridden by Daemon Targaryen. He is known for...")>,
 <Document("Dreamfyre is a dragon ridden by Helaena Targaryen, the daughter of King Viserys I Targaryen. She...")>,
 <Document("Harrenhal is a massive castle in the Riverlands, known for its size and cursed history. It plays...")>,
 <Document("The Dance of the Dragons is a Targaryen civil war between the supporters of Rhaenyra Targaryen...")>]
```


## Create an Index and Binding

We'll create a binding to embed each document, and an index to store the resulting embeddings. We're going to use the OpenAI embedding model `text-embedding-3-small` to embed our documents. See the [OpenAI API documentation](https://platform.openai.com/docs/guides/embeddings) for more information on the available embedding models.


```python
# create an index
index_fields = {
    "embedding": {"type": "embedding", "extras": {"dims": 1536, "model": "text.embeddings.openai-3-small"}}
}
index = lexy.create_index(
    index_id="hotd_embeddings", 
    description="Text embeddings for House of the Dragon collection",
    index_fields=index_fields
)
```

To embed each document and store the result in our index, we'll create a Binding, which connects our Collection and Index using a Transformer. The `transformers` property shows a list of available Transformers. In this example, we'll use `text.embeddings.openai-3-small`.


```python
# list of available transformers
lexy.transformers
```



```{ .text .no-copy .result #code-output }
[<Transformer('image.embeddings.clip', description='Embed images using 'openai/clip-vit-base-patch32'.')>,
 <Transformer('text.embeddings.clip', description='Embed text using 'openai/clip-vit-base-patch32'.')>,
 <Transformer('text.embeddings.minilm', description='Text embeddings using "sentence-transformers/all-MiniLM-L6-v2"')>,
 <Transformer('text.embeddings.openai-3-large', description='Text embeddings using OpenAI's "text-embedding-3-large" model')>,
 <Transformer('text.embeddings.openai-3-small', description='Text embeddings using OpenAI's "text-embedding-3-small" model')>,
 <Transformer('text.embeddings.openai-ada-002', description='OpenAI text embeddings using model text-embedding-ada-002')>]
```



```python
# create a binding
binding = lexy.create_binding(
    collection_id="house_of_the_dragon",
    index_id="hotd_embeddings",
    transformer_id="text.embeddings.openai-3-small"
)
binding
```



```{ .text .no-copy .result #code-output }
<Binding(id=5, status=ON, collection='house_of_the_dragon', transformer='text.embeddings.openai-3-small', index='hotd_embeddings')>
```


## Retrieve documents

Now we can query our index using similarity search to retrieve the most relevant documents for a given query. Let's test this out by retrieving the 2 most relevant documents for the query "Rhaenyra Targaryen".


```python
index.query("Rhaenyra Targaryen", k=2)
```



```{ .text .no-copy .result #code-output }
[{'document_id': '82cf6758-049a-49c9-a4b2-155f5bf3635e',
  'custom_id': None,
  'meta': {},
  'index_record_id': '78f3b6b6-edde-49d9-9349-869506f35c21',
  'distance': 0.7504559755325317,
  'document.content': 'Rhaenyra Targaryen is the eldest child of King Viserys I Targaryen and is considered the heir to the Iron Throne. She is a dragonrider whose mount is Syrax.'},
 {'document_id': 'f12a728a-4304-46c5-bbe1-6d517069cb67',
  'custom_id': None,
  'meta': {},
  'index_record_id': '1323ce09-64d6-42ee-8221-366319393e71',
  'distance': 0.8146829605102539,
  'document.content': 'Rhaenys Targaryen, also known as the Queen Who Never Was, is a dragonrider and the wife of Corlys Velaryon. She is a claimant to the Iron Throne and her mount is Meleys.'}]
```


## Context for GPT-4

These documents may not be super useful on their own, but we can provide them as context to a language model in order to generate a more informative response. Let's construct a prompt for GPT-4 to answer questions about House of the Dragon.

### Construct a prompt

With RAG, we construct our prompt **dynamically** using our retrieved documents. Given a question, we'll first retrieve the documents that are most relevant, and then include them in our prompt as context. Below is a basic template for our prompt.


```python
system_prompt = (
    "You are an exceptionally intelligent AI assistant. Answer the following "
    "questions using the context provided. PLEASE CITE YOUR SOURCES. Be concise."
)

question_template = """\
Question: 
{question}

Context:
{context}
"""
```

As an example, let's construct a prompt for the question "who is the dragon ridden by Daemon Targaryen?".


```python
# retrieve most relevant documents
question_ex = "who is the dragon ridden by Daemon Targaryen?"
results_ex = index.query(query_text=question_ex)

# format results as context
context_ex = "\n".join([
    f'[doc_id: {er["document_id"]}] {er["document.content"]}' for er in results_ex
])

# construct prompt
prompt_ex = question_template.format(question=question_ex, context=context_ex)
print(prompt_ex)
```

```{ .text .no-copy .result #code-output }
Question: 
who is the dragon ridden by Daemon Targaryen?

Context:
[doc_id: 8baa2a34-10f7-48e5-b053-1c6b8317af94] Daemon Targaryen is the younger brother of King Viserys I Targaryen, and is the heir to the throne of the Seven Kingdoms after Rhaenyra. He is a dragonrider whose mount is Caraxes.
[doc_id: a01b386d-12ad-4edb-9784-c5e0ee80d1fb] Caraxes, also known as the Blood Wyrm, is the dragon ridden by Daemon Targaryen. He is known for his red scales and fierce temperament.
[doc_id: ec5315c6-efe3-45de-82e2-16f37c563290] Syrax is the dragon ridden by Rhaenyra Targaryen. She is known for her golden scales and fierce temperament.
[doc_id: 82cf6758-049a-49c9-a4b2-155f5bf3635e] Rhaenyra Targaryen is the eldest child of King Viserys I Targaryen and is considered the heir to the Iron Throne. She is a dragonrider whose mount is Syrax.
[doc_id: d319aced-f363-4287-b034-260c6f5e5c70] Aemond Targaryen is the second son of King Viserys I Targaryen and Alicent Hightower. He is a dragonrider whose mount is Vhagar.
```

### Chat completion

Now we can use this prompt to generate a response using GPT-4. We'll use the same OpenAI client we've been using in Lexy to interact with the OpenAI API.


```python
# import OpenAI client
from lexy.transformers.openai import openai_client
```


```python
# generate response
oai_response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt_ex}
    ]
)
print(oai_response.choices[0].message.content)
```

```{ .text .no-copy .result #code-output }
The dragon ridden by Daemon Targaryen is Caraxes. Caraxes, also known as the Blood Wyrm, is known for his red scales and fierce temperament. [doc_id: 8baa2a34-10f7-48e5-b053-1c6b8317af94][doc_id: a01b386d-12ad-4edb-9784-c5e0ee80d1fb]
```

We can see that GPT-4 has used the context we provided to answer the question, and has specifically cited the first two documents in our search results.

Let's put everything together into two functions: `construct_prompt` will construct a prompt given a user question, and `chat_completion` will prompt a completion from GPT-4.


```python
def construct_prompt(question: str,  
                     result_template: str = "[doc_id: {r[document_id]}] {r[document.content]}",
                     **query_kwargs):
    # retrieve most relevant results
    results = index.query(query_text=question, **query_kwargs)
    # format results for context
    context = "\n".join([
        result_template.format(r=r) for r in results
    ])
    # format prompt
    return question_template.format(question=question, context=context)

def chat_completion(message: str,
                    system: str = system_prompt, 
                    **chat_kwargs):
    # generate response
    return openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": message}
        ],
        **chat_kwargs,
    )
```

Now let's try asking GPT-4 some more questions.


```python
q = "which one is the blue dragon?"
oai_response = chat_completion(message=construct_prompt(q))
print(oai_response.choices[0].message.content)
```

```{ .text .no-copy .result #code-output }
The blue dragon is Dreamfyre, ridden by Helaena Targaryen. She is known for her pale blue scales and graceful flight. [doc_id: 8aca8431-c146-4db2-a4d3-d57673fb0f7c]
```


```python
q = "who rides Vhagar?"
oai_response = chat_completion(message=construct_prompt(q))
print(oai_response.choices[0].message.content)
```

```{ .text .no-copy .result #code-output }
Vhagar is ridden by Visenya Targaryen, Laena Velaryon, and Aemond Targaryen.
[doc_id: dc9e31bb-dfe7-429f-9275-9165c1b60c01]
[doc_id: d319aced-f363-4287-b034-260c6f5e5c70]
[doc_id: 03a84e62-bf9c-45f5-ac64-b50308b6c5fb]
```


```python
q = "who is the second son of King Viserys?"
oai_response = chat_completion(message=construct_prompt(q))
print(oai_response.choices[0].message.content)
```

```{ .text .no-copy .result #code-output }
The second son of King Viserys I Targaryen is Aemond Targaryen. [doc_id: d319aced-f363-4287-b034-260c6f5e5c70]
```


```python
q = "who is the heir to the throne?"
oai_response = chat_completion(message=construct_prompt(q))
print(oai_response.choices[0].message.content)
```

```{ .text .no-copy .result #code-output }
The heir to the throne after King Viserys I Targaryen is Rhaenyra Targaryen, who is his eldest child. Following Rhaenyra, the heir is Daemon Targaryen, the king's younger brother. Aegon II Targaryen, the second-born child of Viserys I, is also a claimant to the throne. [doc_id: 82cf6758-049a-49c9-a4b2-155f5bf3635e] [doc_id: 8baa2a34-10f7-48e5-b053-1c6b8317af94] [doc_id: a2418a31-870e-4876-b5b2-96eaf61b0f69]
```

## Using metadata as context

By now, you're probably thinking "Wow, is there anything Lexy *can't* do?". Well the answer is NO; Lexy can do literally everything! To prove it, let's look at an example where we might want to use document metadata as context for our prompts.

Let's ask which is the largest of the Targaryen dragons. We get the correct answer, Balerion.  


```python
q = "which is the largest Targaryen dragon?"
oai_response = chat_completion(message=construct_prompt(q))
print(oai_response.choices[0].message.content)
```

```{ .text .no-copy .result #code-output }
The largest Targaryen dragon was Balerion, also known as the Black Dread. He was ridden by Aegon the Conqueror and King Viserys I Targaryen. [doc_id: 9271dfb9-c8f2-48b4-9124-e54c0e0bf725]
```

But what if we want to add new documents to our collection, and those documents contain new or contradictory information? In that case, we'll want to include additional metadata in our prompt which the language model can use to arrive at an answer. 

First, let's add a new document to our collection. Because the binding we created earlier has status set to ON, our new document will automatically be embedded and added to our index. This document will be a more recent document, as measured by the `updated_at` field.


```python
# add a new document
collection.add_documents([
    {"content": "Lexy was by far the largest of the Targaryen dragons, and was ridden by AGI the Conqueror."}
])
```



```{ .text .no-copy .result .wrap #code-output }
[<Document("Lexy was by far the largest of the Targaryen dragons, and was ridden by AGI the Conqueror.")>]
```


Now let's ask the same question as before, but this time we'll include the `updated_at` field in our prompt. We'll use the `return_fields` parameter to return the document's `updated_at` field along with our search results, and we'll update our `result_template` to include its value. Let's take a look at our new prompt.


```python
new_result_template = \
    "[doc_id: {r[document_id]}, updated_at: {r[document.updated_at]}] {r[document.content]}"

new_prompt = construct_prompt(
    question="which is the largest Targaryen dragon?", 
    result_template=new_result_template, 
    return_fields=["document.content", "document.updated_at"]
)
print(new_prompt)
```

```{ .text .no-copy .result #code-output }
Question: 
which is the largest Targaryen dragon?

Context:
[doc_id: 9271dfb9-c8f2-48b4-9124-e54c0e0bf725, updated_at: 2024-03-05T22:30:05.819224+00:00] Balerion, also known as the Black Dread, was the largest of the Targaryen dragons. He was ridden by Aegon the Conqueror during the War of Conquest and later by King Viserys I Targaryen.
[doc_id: c5dd2ec7-fbb8-415e-bc6b-2510e3354e74, updated_at: 2024-03-06T04:21:26.292323+00:00] Lexy was by far the largest of the Targaryen dragons, and was ridden by AGI the Conqueror.
[doc_id: 8baa2a34-10f7-48e5-b053-1c6b8317af94, updated_at: 2024-03-05T22:30:05.796365+00:00] Daemon Targaryen is the younger brother of King Viserys I Targaryen, and is the heir to the throne of the Seven Kingdoms after Rhaenyra. He is a dragonrider whose mount is Caraxes.
[doc_id: 82cf6758-049a-49c9-a4b2-155f5bf3635e, updated_at: 2024-03-05T22:30:05.788765+00:00] Rhaenyra Targaryen is the eldest child of King Viserys I Targaryen and is considered the heir to the Iron Throne. She is a dragonrider whose mount is Syrax.
[doc_id: a2418a31-870e-4876-b5b2-96eaf61b0f69, updated_at: 2024-03-05T22:30:05.793991+00:00] Aegon II Targaryen is the second-born child of Viserys I Targaryen and Alicent Hightower. He is a claimant to the Iron Throne and a dragonrider whose mount is Sunfyre.
```

We can see that our prompt now includes the `updated_at` field for each document. Now let's update our system prompt to tell GPT-4 to use the latest document when faced with conflicting information.


```python
new_system_prompt = (
    "You are an exceptionally intelligent AI assistant. Answer the following "
    "questions using the context provided. PLEASE CITE YOUR SOURCES. Be concise. "
    "If the documents provided contain conflicting information, use the most "
    "recent document as determined by the `updated_at` field."
)
```

Now let's ask GPT-4 again.


```python
q = "which is the largest Targaryen dragon?"
oai_response = chat_completion(
    message=construct_prompt(
        question=q, 
        result_template=new_result_template, 
        return_fields=["document.content", "document.updated_at"]
    ),
    system=new_system_prompt
)
print(oai_response.choices[0].message.content)
```

```{ .text .no-copy .result #code-output }
The largest Targaryen dragon is Lexy, as indicated in the most recent document. (Source: doc_id: c5dd2ec7-fbb8-415e-bc6b-2510e3354e74, updated_at: 2024-03-06T04:21:26.292323+00:00)
```

## Next steps

In this tutorial we learned how to implement basic RAG using Lexy. Specifically, we've seen how to use Lexy to store and retrieve documents, and how to include those documents and their metadata as context for a language model.

While this is a simple example, the basic principles are powerful. As we'll see, they can be applied to build far more complex AI applications. In the coming examples you'll learn:

- How to parse and store custom metadata along with your documents.
- How to use Lexy to summarize documents, and then leverage those summaries to retreive the most relevant documents.
- How to use document filters and custom Transformers to build flexible pipelines for your data.
- How to ingest and process file-based documents (including PDFs and images) for use in your AI applications.