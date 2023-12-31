# polyglot c headers

Inspired by : [你写过的最蠢的代码是？ - 参水猿的回答 - 知乎](https://www.zhihu.com/question/463190146/answer/2769772491)

[中文Readme](./Readme.md)

### Feature

generate a mp4 file that is also a c++ header, which plays the video itself.

We also have scripts to do similar work on bash scripts(for linux) or PE (for windows) executables.

### Usage

`python3 ./scripts/build_mp4.py input.mp4 output.mp4 -p -b`

### Example

![demo](./demo.webp)

### How it works

###### C++ side

C++ has an awesome feature called raw string literals. Basically, this feature lets us include a long binary content inside a string literal.

We could write something like this:

```
void f(){(void)R"d_sequence(
    put binary data here!
)d_sequence";}
```



Besides, frequently-used c++ compilers ignore null characters in source files.

These two features are all we need on the c++ side.

##### mp4 side

A mp4 file is made up of so-called 'atom's, each atom contains a four-byte size plus a four-byte tag at the beginning.

The standard requires the `ftyp` atom to appear after only necessary signatures, before any significant atom, and as early as possible.

By testing, we can see that inserting a few bytes of an unknown atom, and a maybe longer `skip` atom in front of the mp4 file does not corrupt the file.

We consider an atom like below:

```
00 00 00 20 2f 2f 61 61 0a 20 20 20 20 20 20 20
20 20 20 20 20 20 20 20 20 20 20 20 20 20 2f 2f
```

it is a 32-byte atom tagged '//aa'. 

And it can be interpreted as string '\0\0\0 //aa\n  ...... //'.

As mentioned earlier, null bytes are ignored. So this atom (as header file) contains of only spaces and comments, and has no meaning. 

What's more, it leaves a single-line comment open, thus comments out next line in file.

After this atom, we add a longer (2304 bytes) `skip` atom, constructed like below:

```
00 00 09 00 73 6b 69 70 0a ......
```

which is string "\0\0\t\0skip\n". Ignoring null bytes, it contains only printable characters, and is certainly commented out by the last atom's trailing '//'

Now we can put in about two kilobytes of c++ code without corrupting the mp4 file. we 'open' a raw string literal.

And, at the end of the mp4 file, we append an atom to 'close' the string literal. This atom has its size and tag wrapped inside the string literal, so we do not need to worry about them.

To sum up, we have something like this, which is both a valid mp4 file and a c++ header.

```
<NUL><NUL><NUL>//aa
              //<NUL><NUL>    <NUL>skip
some_c++_code (mainly pragmas and defines)
void f(){(void)R"--------(
    lots_of_binary_data
[four bytes of last atom size][some meaningless atom name]
--------)";}
c++ code to declare the original mp4 as const array or base64 string
c++ code to decode the video and invoke ffplay
```

###### bash scripts

So far we can only embed mp4 files. And that highly relies on the mp4 format. Can we do something more 'extensible' ? For example, embed any 'resource' in, and use a certain program to open it.

And here we come up with shell scripts.

Things are a lot easier because shell scripts see lines starting with '#' as comments, so we can put a lot of preprocessor directives inside without affecting the script.

If we try to play something tricky, we can define some macro like below:

```
#define echo void f(){(void)
echo R"------(">/dev/null
    original_script
exit 0
)------";
......
```

But now we are just playing with scripts generated by our script. We can make sure that the script does not contain lines that can be interpreted as c++ preprocessor directives, so let's do it simple: just add an `exit 0` , and wrap the script in a pair of `#if 0` and `#endif`.

The script dumps a certain range of bytes from the script itself, decodes these extracted bytes using base64 decoder, and executes the decoded file with given interpreter.

After the script, we put the base64 of original resource, in forms of c strings. System base64 decoder will ignore non-alphabet characters, so quotes, commas and line endings will not affect the result of the decoder.

And in the end we put some c++ code to decode and open the resource.

###### Windows executables

The above method only applies to linux system (or at most, a few systems that has GNU coreutils and can execute sh-compilant scripts.)

So we now want to find a way to embed windows executables.

The first big problem is the 'MZ' magic bytes. Well, I cannot think how a c++ source file can begin with these two characters. Maybe some old C standards allow declaring a function without return type, but that is obviously not possible in recent compilers.

So I give up. Just define it to nothing before including the header. 

We can even add a error message if the user forgets to do so: preprocessor raises errors at [translation phase 4](https://en.cppreference.com/w/cpp/language/translation_phases), while syntactical and semantical analysis takes place during phase 7. So we raise the error earlier!

Luckily, most bytes inside the dos header are unused. Only the first two and last four bytes are meaningful. So after the first 'MZ' bytes, we wrap the last four bytes inside a raw string literal.

The dos stub is not so limited in size. We close the previous raw string literal, put some c++ code here, and open another raw string literal to wrap the rest of the executable.

And we modify the PE header to insert a new section at the end, which closes the string literal, and declares helper functions to write the executable to a temporary file and execute.

### Limitations

MSVC does not support files containing byte 0x1A. For historic reasons, it sees byte 0x1A as EOF.

clang-cl compiles dog slow when binary file grows in size. Better use mingw gcc instead.

### License

The downloaded resources are not part of this repository. Obey licenses of their providers.

The other parts in this repository are under [WTFPL](http://www.wtfpl.net/txt/copying)
