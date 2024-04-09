# Multimodal image search

In this tutorial, we'll walk through how to use Lexy to create a multimodal search application. We'll use the [CLIP](https://openai.com/blog/clip/) model from OpenAI to create embeddings for images, and then use those embeddings to find matching images for a given text query, or vice versa.


```python
from lexy_py import LexyClient

lx = LexyClient()
```

## Create collection

Let's first create a collection to store our images. We'll use the **`images_tutorial`** collection for this tutorial.


```python
# create a new collection
images_tutorial = lx.create_collection('images_tutorial')
images_tutorial
```



```{ .text .no-copy .result #code-output }
<Collection('images_tutorial', description='None')>
```


## Create index and binding

### Define index

First we'll define our index to store our embedded images. We use **`*.embeddings.clip`** as the transformer model name 
to indicate that we want to use the CLIP embeddings model, but that the embedding field can use any model that matches 
this pattern, including **`image.embeddings.clip`** and **`text.embeddings.clip`**. 


```python
# define index fields
index_fields = {
    "embedding": {"type": "embedding", "extras": {"dims": 512, "model": "*.embeddings.clip"}},
}

# create index
idx = lx.create_index(
    index_id='image_tutorial_index', 
    description='Index for images tutorial',
    index_fields=index_fields
)
idx
```



```{ .text .no-copy .result #code-output }
<Index('image_tutorial_index', description='Index for images tutorial')>
```


We'll use the CLIP image embeddings transformer available on [HuggingFace](https://huggingface.co/openai/clip-vit-base-patch32). This transformer uses the [CLIP](https://openai.com/blog/clip/) model from OpenAI to create embeddings for images. 

The CLIP model is a transformer model that was trained on a large dataset of images and text pairs. The model learns to map images and text to a shared embedding space, where the embeddings of matching images and text are close together. We can use this model to create embeddings for images, and then use those embeddings to find matching images for a given text query, or vice versa.


```python
lx.transformers
```



```{ .text .no-copy .result #code-output }
[<Transformer('image.embeddings.clip', description='Embed images using 'openai/clip-vit-base-patch32'.')>,
 <Transformer('text.embeddings.clip', description='Embed text using 'openai/clip-vit-base-patch32'.')>,
 <Transformer('text.embeddings.minilm', description='Text embeddings using "sentence-transformers/all-MiniLM-L6-v2"')>,
 <Transformer('text.embeddings.openai-3-large', description='Text embeddings using OpenAI's "text-embedding-3-large" model')>,
 <Transformer('text.embeddings.openai-3-small', description='Text embeddings using OpenAI's "text-embedding-3-small" model')>,
 <Transformer('text.embeddings.openai-ada-002', description='OpenAI text embeddings using model text-embedding-ada-002')>]
```


### Create binding

We'll create a binding that will process images added to our **`images_tutorial`** collection using the CLIP image 
embeddings transformer, and store the results in **`image_tutorial_index`**.


```python
binding = lx.create_binding(
    collection_name='images_tutorial',
    transformer_id='image.embeddings.clip',
    index_id='image_tutorial_index'
)
binding
```



```{ .text .no-copy .result #code-output }
<Binding(id=3, status=ON, collection='images_tutorial', transformer='image.embeddings.clip', index='image_tutorial_index')>
```



## Upload images to the collection

Let's upload some images from the [image-text-demo dataset](https://huggingface.co/datasets/shabani1/image-text-demo) to the collection. This dataset is from HuggingFace 
datasets and requires the `datasets` package to be installed.


```python
! pip install datasets
```


```python
# import test data from HuggingFace datasets - requires `pip install datasets`

from datasets import load_dataset
data = load_dataset("shabani1/image-text-demo", split="train")
```


```python
len(data)
```



```{ .text .no-copy .result #code-output }
21
```



```python
# add documents to the collection
for i, row in enumerate(data, start=1):
    print(i, row['text'])
    lx.upload_documents(files=row['image'], 
                        filenames=row['text'] + '.jpg', 
                        collection_name='images_tutorial')
```

```{ .text .no-copy .result #code-output }
1 aerial shot of futuristic city with large motorway
2 aerial shot of modern city at sunrise
3 butterfly landing on the nose of a cat
4 cute kitten walking through long grass
5 fluffy dog sticking out tongue with yellow background
6 futuristic city with led lit tower blocks
7 futuristic wet city street after rain with red and blue lights
8 ginger striped cat with long whiskers laid on wooden table
9 happy dog walking through park area holding ball
10 happy ginger dog sticking out its tongue sat in front of dirt path
11 happy small fluffy white dog running across grass
12 kitten raising paw to sky with cyan background
13 modern city skyline at sunrise with pink to blue sky
14 modern neon lit city alleyway
15 new york city street view with yellow cabs
16 puppy with big ears sat with orange background
17 suburban area with city skyline in distance
18 three young dogs on dirt road
19 top down shot of black and white cat with yellow background
20 two dogs playing in the snow
21 two dogs running on dirt path
```


```python
# check the collection
images_tutorial.list_documents()
```



```{ .text .no-copy .result #code-output }
[<Document("<Image(aerial shot of futuristic city with large motorway.jpg)>")>,
 <Document("<Image(aerial shot of modern city at sunrise.jpg)>")>,
 <Document("<Image(butterfly landing on the nose of a cat.jpg)>")>,
 <Document("<Image(cute kitten walking through long grass.jpg)>")>,
 <Document("<Image(fluffy dog sticking out tongue with yellow background.jpg)>")>,
 <Document("<Image(futuristic city with led lit tower blocks.jpg)>")>,
 <Document("<Image(futuristic wet city street after rain with red and blue lights.jpg)>")>,
 <Document("<Image(ginger striped cat with long whiskers laid on wooden table.jpg)>")>,
 <Document("<Image(happy dog walking through park area holding ball.jpg)>")>,
 <Document("<Image(happy ginger dog sticking out its tongue sat in front of dirt path.jpg)>")>,
 <Document("<Image(happy small fluffy white dog running across grass.jpg)>")>,
 <Document("<Image(kitten raising paw to sky with cyan background.jpg)>")>,
 <Document("<Image(modern city skyline at sunrise with pink to blue sky.jpg)>")>,
 <Document("<Image(modern neon lit city alleyway.jpg)>")>,
 <Document("<Image(new york city street view with yellow cabs.jpg)>")>,
 <Document("<Image(puppy with big ears sat with orange background.jpg)>")>,
 <Document("<Image(suburban area with city skyline in distance.jpg)>")>,
 <Document("<Image(three young dogs on dirt road.jpg)>")>,
 <Document("<Image(top down shot of black and white cat with yellow background.jpg)>")>,
 <Document("<Image(two dogs playing in the snow.jpg)>")>,
 <Document("<Image(two dogs running on dirt path.jpg)>")>]
```


## Query index

Let's first define some helper functions to display our image results.


```python
import httpx
from IPython.display import display, HTML
from PIL import Image

def image_from_url(url): 
    response = httpx.get(url)
    response.raise_for_status()
    return Image.open(response)

def display_results_html(records):
    html_content = ""
    for r in records:
        d = r['document']
        thumbnail_url = d.thumbnail_url
        fname = d.meta.get('filename')
        score = f"score: {r['distance']:.4f}"
        # Creating a row for each result with image on the left and text on the right
        html_content += f"""
        <div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
            <img src='{thumbnail_url}' style='width: auto; height: auto; margin-right: 20px;'/>
            <div>
                <p>{fname}</p>
                <p>{score}</p>
            </div>
        </div>
        """
    # Display all results as HTML
    display(HTML(html_content))

```

### Query by text

We can query our index by text to find matching images.


```python
results = idx.query(query_text='best friends', return_document=True)
display_results_html(results)
```


<div id="code-output" class="result">

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/two%20dogs%20playing%20in%20the%20snow.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>two dogs playing in the snow.jpg</p>
        <p>score: 13.4786</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/three%20young%20dogs%20on%20dirt%20road.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>three young dogs on dirt road.jpg</p>
        <p>score: 13.8796</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/two%20dogs%20running%20on%20dirt%20path.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>two dogs running on dirt path.jpg</p>
        <p>score: 13.9199</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/happy%20ginger%20dog%20sticking%20out%20its%20tongue%20sat%20in%20front%20of%20dirt%20path.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>happy ginger dog sticking out its tongue sat in front of dirt path.jpg</p>
        <p>score: 14.1915</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/ginger%20striped%20cat%20with%20long%20whiskers%20laid%20on%20wooden%20table.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>ginger striped cat with long whiskers laid on wooden table.jpg</p>
        <p>score: 14.2613</p>
    </div>
</div>

</div>



```python
results = idx.query(query_text='gotham city', return_document=True)
display_results_html(results)
```


<div id="code-output" class="result">

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/aerial%20shot%20of%20modern%20city%20at%20sunrise.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>aerial shot of modern city at sunrise.jpg</p>
        <p>score: 12.9919</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/suburban%20area%20with%20city%20skyline%20in%20distance.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>suburban area with city skyline in distance.jpg</p>
        <p>score: 13.0167</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/modern%20city%20skyline%20at%20sunrise%20with%20pink%20to%20blue%20sky.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>modern city skyline at sunrise with pink to blue sky.jpg</p>
        <p>score: 13.0856</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/aerial%20shot%20of%20futuristic%20city%20with%20large%20motorway.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>aerial shot of futuristic city with large motorway.jpg</p>
        <p>score: 13.2318</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/futuristic%20wet%20city%20street%20after%20rain%20with%20red%20and%20blue%20lights.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>futuristic wet city street after rain with red and blue lights.jpg</p>
        <p>score: 13.2840</p>
    </div>
</div>

</div>


### Query by image

We can also query our index by image to find matching images.


```python
img = image_from_url('https://getlexy.com/assets/images/dalle-agi.jpeg')
img
```



<div id="code-output" class="result">
<img src="https://getlexy.com/assets/images/dalle-agi.jpeg" style='width: auto; height: auto; margin-right: 20px; margin-top: 20px; margin-bottom: 20px;'>
</div>



```python
results = idx.query(query_image=img, return_document=True)
display_results_html(results)
```


<div id="code-output" class="result">

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/butterfly%20landing%20on%20the%20nose%20of%20a%20cat.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>butterfly landing on the nose of a cat.jpg</p>
        <p>score: 8.9913</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/puppy%20with%20big%20ears%20sat%20with%20orange%20background.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>puppy with big ears sat with orange background.jpg</p>
        <p>score: 9.2752</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/fluffy%20dog%20sticking%20out%20tongue%20with%20yellow%20background.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>fluffy dog sticking out tongue with yellow background.jpg</p>
        <p>score: 9.3786</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/two%20dogs%20running%20on%20dirt%20path.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>two dogs running on dirt path.jpg</p>
        <p>score: 9.5351</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/cute%20kitten%20walking%20through%20long%20grass.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>cute kitten walking through long grass.jpg</p>
        <p>score: 9.6472</p>
    </div>
</div>

</div>


```python
img = image_from_url('https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Night_in_the_Greater_Tokyo_Area_ISS054.jpg/2560px-Night_in_the_Greater_Tokyo_Area_ISS054.jpg')
img
```




<div id="code-output" class="result">
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Night_in_the_Greater_Tokyo_Area_ISS054.jpg/2560px-Night_in_the_Greater_Tokyo_Area_ISS054.jpg" style='width: auto; height: auto; margin-right: 20px; margin-top: 20px; margin-bottom: 20px;'>
</div>



```python
results = idx.query(query_image=img, return_document=True)
display_results_html(results)
```


<div id="code-output" class="result">

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/suburban%20area%20with%20city%20skyline%20in%20distance.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>suburban area with city skyline in distance.jpg</p>
        <p>score: 7.7127</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/futuristic%20city%20with%20led%20lit%20tower%20blocks.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>futuristic city with led lit tower blocks.jpg</p>
        <p>score: 8.0037</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/aerial%20shot%20of%20futuristic%20city%20with%20large%20motorway.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>aerial shot of futuristic city with large motorway.jpg</p>
        <p>score: 8.3442</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/modern%20city%20skyline%20at%20sunrise%20with%20pink%20to%20blue%20sky.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>modern city skyline at sunrise with pink to blue sky.jpg</p>
        <p>score: 8.4371</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/aerial%20shot%20of%20modern%20city%20at%20sunrise.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>aerial shot of modern city at sunrise.jpg</p>
        <p>score: 8.9889</p>
    </div>
</div>

</div>



```python
img = image_from_url('https://upload.wikimedia.org/wikipedia/commons/e/ed/Shanghai_skyline_2018%28cropped%29.jpg')
img
```



<div id="code-output" class="result">
<img src="https://upload.wikimedia.org/wikipedia/commons/e/ed/Shanghai_skyline_2018%28cropped%29.jpg" style='width: auto; height: auto; margin-right: 20px; margin-top: 20px; margin-bottom: 20px;'>
</div>




```python
results = idx.query(query_image=img, return_document=True)
display_results_html(results)
```


<div id="code-output" class="result">

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/aerial%20shot%20of%20futuristic%20city%20with%20large%20motorway.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>aerial shot of futuristic city with large motorway.jpg</p>
        <p>score: 6.2110</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/futuristic%20city%20with%20led%20lit%20tower%20blocks.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>futuristic city with led lit tower blocks.jpg</p>
        <p>score: 6.7713</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/aerial%20shot%20of%20modern%20city%20at%20sunrise.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>aerial shot of modern city at sunrise.jpg</p>
        <p>score: 7.0736</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/modern%20city%20skyline%20at%20sunrise%20with%20pink%20to%20blue%20sky.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>modern city skyline at sunrise with pink to blue sky.jpg</p>
        <p>score: 7.4314</p>
    </div>
</div>

<div style='display: flex; align-items: center; margin-bottom: 20px; margin-top: 20px;'>
    <img src='/assets/images/new%20york%20city%20street%20view%20with%20yellow%20cabs.jpg' style='width: auto; height: auto; margin-right: 20px;'/>
    <div>
        <p>new york city street view with yellow cabs.jpg</p>
        <p>score: 7.8167</p>
    </div>
</div>

</div>

